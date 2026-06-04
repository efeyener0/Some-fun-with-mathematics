/**
 * @file cebir_viewer.cpp
 * @brief High-performance, zero-dependency 3D PLY Point Cloud Viewer using
 *        native Win32 API and raw OpenGL.
 * 
 * Links against system libraries opengl32.lib, glu32.lib, user32.lib, and gdi32.lib.
 * Compiles out-of-the-box on Windows without any third-party dependencies!
 */

#ifndef UNICODE
#define UNICODE
#endif

#include <windows.h>
#include <GL/gl.h>
#include <GL/glu.h>
#include <iostream>
#include <fstream>
#include <vector>
#include <string>
#include <sstream>

// Automatically instruct MSVC to link built-in Windows system libraries
#pragma comment(lib, "opengl32.lib")
#pragma comment(lib, "glu32.lib")
#pragma comment(lib, "user32.lib")
#pragma comment(lib, "gdi32.lib")

// Vertex structure matching our PLY point cloud format
struct Vertex {
    float x, y, z;
    unsigned char r, g, b;
};

// Global variables for viewer state
std::vector<Vertex> g_vertices;
float g_rotX = 25.0f;
float g_rotY = -45.0f;
float g_zoom = -6.0f;
float g_panX = 0.0f;
float g_panY = 0.0f;
int g_lastMouseX = 0;
int g_lastMouseY = 0;
bool g_isRotating = false;
bool g_isPanning = false;

// Function to parse the PLY point cloud file
bool load_ply_file(const std::wstring& filename, std::vector<Vertex>& vertices) {
    std::ifstream in(filename, std::ios::in);
    if (!in.is_open()) {
        return false;
    }

    std::string line;
    size_t vertex_count = 0;
    bool header_ended = false;

    // 1. Read PLY Header
    while (std::getline(in, line)) {
        if (line.find("element vertex") == 0) {
            std::stringstream ss(line);
            std::string temp1, temp2;
            ss >> temp1 >> temp2 >> vertex_count;
        } else if (line.find("end_header") == 0) {
            header_ended = true;
            break;
        }
    }

    if (!header_ended || vertex_count == 0) {
        return false;
    }

    vertices.reserve(vertex_count);

    // 2. Read Vertex coordinates and RGB colors
    float x, y, z;
    int r, g, b;
    for (size_t i = 0; i < vertex_count; ++i) {
        if (!(in >> x >> y >> z >> r >> g >> b)) {
            break;
        }
        Vertex v;
        v.x = x;
        v.y = y;
        v.z = z;
        v.r = (unsigned char)r;
        v.g = (unsigned char)g;
        v.b = (unsigned char)b;
        vertices.push_back(v);
    }

    return true;
}

// Set up OpenGL Pixel Format for the Windows device context
void setup_pixel_format(HDC hDC) {
    PIXELFORMATDESCRIPTOR pfd = {
        sizeof(PIXELFORMATDESCRIPTOR),
        1,
        PFD_DRAW_TO_WINDOW | PFD_SUPPORT_OPENGL | PFD_DOUBLEBUFFER,
        PFD_TYPE_RGBA,
        32,
        0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0,
        24, // 24-bit depth buffer
        8,  // 8-bit stencil buffer
        0, PFD_MAIN_PLANE, 0, 0, 0, 0
    };

    int pixelFormat = ChoosePixelFormat(hDC, &pfd);
    SetPixelFormat(hDC, pixelFormat, &pfd);
}

// Window Procedure to handle input and redraws
LRESULT CALLBACK WndProc(HWND hWnd, UINT message, WPARAM wParam, LPARAM lParam) {
    static HDC hDC;
    static HGLRC hRC;

    switch (message) {
        case WM_CREATE:
            hDC = GetDC(hWnd);
            setup_pixel_format(hDC);
            hRC = wglCreateContext(hDC);
            wglMakeCurrent(hDC, hRC);

            // Initialize OpenGL settings
            glEnable(GL_DEPTH_TEST);
            glEnable(GL_POINT_SMOOTH);
            glPointSize(2.0f); // Render points with smooth glowing aesthetic
            glClearColor(0.01f, 0.03f, 0.07f, 1.0f); // Deep space dark background
            break;

        case WM_CLOSE:
            wglMakeCurrent(NULL, NULL);
            wglDeleteContext(hRC);
            ReleaseDC(hWnd, hDC);
            DestroyWindow(hWnd);
            break;

        case WM_DESTROY:
            PostQuitMessage(0);
            break;

        case WM_SIZE: {
            int width = LOWORD(lParam);
            int height = HIWORD(lParam);
            if (height == 0) height = 1;

            glViewport(0, 0, width, height);

            glMatrixMode(GL_PROJECTION);
            glLoadIdentity();
            gluPerspective(45.0, (double)width / (double)height, 0.1, 100.0);

            glMatrixMode(GL_MODELVIEW);
            break;
        }

        case WM_LBUTTONDOWN:
            g_lastMouseX = LOWORD(lParam);
            g_lastMouseY = HIWORD(lParam);
            g_isRotating = true;
            SetCapture(hWnd);
            break;

        case WM_LBUTTONUP:
            g_isRotating = false;
            ReleaseCapture();
            break;

        case WM_RBUTTONDOWN:
            g_lastMouseX = LOWORD(lParam);
            g_lastMouseY = HIWORD(lParam);
            g_isPanning = true;
            SetCapture(hWnd);
            break;

        case WM_RBUTTONUP:
            g_isPanning = false;
            ReleaseCapture();
            break;

        case WM_MOUSEMOVE: {
            int x = LOWORD(lParam);
            int y = HIWORD(lParam);

            if (g_isRotating) {
                g_rotY += (x - g_lastMouseX) * 0.5f;
                g_rotX += (y - g_lastMouseY) * 0.5f;
                InvalidateRect(hWnd, NULL, FALSE);
            } else if (g_isPanning) {
                g_panX += (x - g_lastMouseX) * 0.01f;
                g_panY -= (y - g_lastMouseY) * 0.01f;
                InvalidateRect(hWnd, NULL, FALSE);
            }

            g_lastMouseX = x;
            g_lastMouseY = y;
            break;
        }

        case WM_MOUSEWHEEL: {
            int zDelta = GET_WHEEL_DELTA_WPARAM(wParam);
            g_zoom += zDelta * 0.005f;
            InvalidateRect(hWnd, NULL, FALSE);
            break;
        }

        case WM_KEYDOWN:
            if (wParam == 'R') {
                // Reset view
                g_rotX = 25.0f;
                g_rotY = -45.0f;
                g_zoom = -6.0f;
                g_panX = 0.0f;
                g_panY = 0.0f;
                InvalidateRect(hWnd, NULL, FALSE);
            }
            break;

        case WM_PAINT: {
            PAINTSTRUCT ps;
            BeginPaint(hWnd, &ps);

            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
            glLoadIdentity();

            // Apply transformations
            glTranslatef(g_panX, g_panY, g_zoom);
            glRotatef(g_rotX, 1.0f, 0.0f, 0.0f);
            glRotatef(g_rotY, 0.0f, 1.0f, 0.0f);

            // Draw Coordinate Grid Floor
            glBegin(GL_LINES);
            glColor3f(0.1f, 0.2f, 0.3f);
            for (float i = -3.0f; i <= 3.0f; i += 0.5f) {
                glVertex3f(i, -3.0f, -3.0f); glVertex3f(i, -3.0f, 3.0f);
                glVertex3f(-3.0f, -3.0f, i); glVertex3f(3.0f, -3.0f, i);
            }
            glEnd();

            // Render the 3D Point Cloud using raw OpenGL
            if (!g_vertices.empty()) {
                glEnableClientState(GL_VERTEX_ARRAY);
                glEnableClientState(GL_COLOR_ARRAY);

                // Use high-performance OpenGL vertex arrays
                glVertexPointer(3, GL_FLOAT, sizeof(Vertex), &g_vertices[0].x);
                glColorPointer(3, GL_UNSIGNED_BYTE, sizeof(Vertex), &g_vertices[0].r);

                glDrawArrays(GL_POINTS, 0, (GLsizei)g_vertices.size());

                glDisableClientState(GL_COLOR_ARRAY);
                glDisableClientState(GL_VERTEX_ARRAY);
            }

            SwapBuffers(hDC);
            EndPaint(hWnd, &ps);
            break;
        }

        default:
            return DefWindowProc(hWnd, message, wParam, lParam);
    }
    return 0;
}

int WINAPI WinMain(HINSTANCE hInstance, HINSTANCE hPrevInstance, LPSTR lpCmdLine, int nCmdShow) {
    // 1. Parse and Load the 3D PLY Point Cloud File
    std::wstring ply_file = L"holographic_interference_3d.ply";
    
    std::cout << "Loading 3D Point Cloud file: holographic_interference_3d.ply ..." << std::endl;
    if (!load_ply_file(ply_file, g_vertices)) {
        MessageBox(NULL, L"Failed to load 'holographic_interference_3d.ply'!\nPlease run 'cebir_cuda_3d.exe' first to generate the file.", L"Error", MB_OK | MB_ICONERROR);
        return -1;
    }
    std::cout << "Loaded " << g_vertices.size() << " 3D vertices successfully." << std::endl;

    // 2. Register Windows Window Class
    WNDCLASS wc = {};
    wc.lpfnWndProc = WndProc;
    wc.hInstance = hInstance;
    wc.lpszClassName = L"Cebir3DViewerClass";
    wc.hbrBackground = (HBRUSH)(COLOR_BACKGROUND);
    wc.hCursor = LoadCursor(NULL, IDC_ARROW);

    if (!RegisterClass(&wc)) {
        return -1;
    }

    // 3. Create the Window
    HWND hWnd = CreateWindowEx(
        0,
        L"Cebir3DViewerClass",
        L"Cebir 3D Hacimsel Topoloji & Evre Girisimi Görüntüleyici",
        WS_OVERLAPPEDWINDOW,
        CW_USEDEFAULT, CW_USEDEFAULT, 1024, 768,
        NULL, NULL, hInstance, NULL
    );

    if (!hWnd) {
        return -1;
    }

    // Show command console side-by-side or hide it
    ShowWindow(hWnd, nCmdShow);
    UpdateWindow(hWnd);

    // 4. Main Event Loop
    MSG msg;
    while (GetMessage(&msg, NULL, 0, 0)) {
        TranslateMessage(&msg);
        DispatchMessage(&msg);
    }

    return (int)msg.wParam;
}
