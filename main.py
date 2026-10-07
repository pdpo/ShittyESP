# shitty cs2 esp by AK (1.0)
# warning: this is probably detected asf so use at your own risk!

import pymem
import pymem.process
import struct
import pygame
import ctypes
from ctypes import wintypes

# offsets
dwViewMatrix = 0x23CB830
dwEntityList = 0x2571220
dwGameEntitySystem = 0x2571220
dwLocalPlayerController = 0x23A0F30
dwLocalPlayerPawn = 0x23C6268
EntityStride = 0x70
EntityArrayOffset = 0x10

offsets = {
    "m_hPlayerPawn": 0x914,
    "m_iszPlayerName": 0x6F4,
    "m_vOldOrigin": 0x13B8,
    "m_iHealth": 0x34C,
}

#config
config = {
    'enemycolor': (255, 0, 0),
    'teamcolor': (0, 150, 255),
    'tracertype': 'off',
    'boxstyle': 'full',
    'healthbar': True,
    'shownames': True,
}

def read_view_matrix(pm, client_base):
    matrix_bytes = pm.read_bytes(client_base + dwViewMatrix, 64)
    return list(struct.unpack('16f', matrix_bytes))

def world_to_screen(matrix, x, y, z, sw, sh):
    w = x * matrix[12] + y * matrix[13] + z * matrix[14] + matrix[15]
    if w < 0.01:
        return None
    sx = int(sw / 2 + (sw / 2) * (x * matrix[0] + y * matrix[1] + z * matrix[2] + matrix[3]) / w)
    sy = int(sh / 2 - (sh / 2) * (x * matrix[4] + y * matrix[5] + z * matrix[6] + matrix[7]) / w)
    return sx, sy

def get_local_team(pm, client_base):
    try:
        ctrl = pm.read_ulonglong(client_base + dwLocalPlayerController)
        if ctrl:
            val = pm.read_ushort(ctrl + 0x0848)
            if val in (2, 3):
                return val
    except:
        pass
    try:
        pawn = pm.read_ulonglong(client_base + dwLocalPlayerPawn)
        if pawn:
            val = pm.read_ushort(pawn + 0x0E8C)
            if val in (2, 3):
                return val
    except:
        pass
    return 0

def get_team(pm, controller, pawn):
    try:
        val = pm.read_ushort(controller + 0x0848)
        if val in (2, 3):
            return val
    except:
        pass
    try:
        if pawn:
            val = pm.read_ushort(pawn + 0x0E8C)
            if val in (2, 3):
                return val
    except:
        pass
    return 0

def get_game_window():
    hwnd = ctypes.windll.user32.FindWindowW(None, "Counter-Strike 2")
    if not hwnd:
        hwnd = ctypes.windll.user32.FindWindowW("SDL_app", None)
    return hwnd

def init_overlay(parent_hwnd):
    rect = wintypes.RECT()
    ctypes.windll.user32.GetClientRect(parent_hwnd, ctypes.byref(rect))
    width = rect.right - rect.left
    height = rect.bottom - rect.top

    pygame.init()
    screen = pygame.display.set_mode((width, height), pygame.NOFRAME)
    overlay_hwnd = pygame.display.get_wm_info()['window']

    ctypes.windll.user32.SetParent(overlay_hwnd, parent_hwnd)

    style = ctypes.windll.user32.GetWindowLongW(overlay_hwnd, -16)
    style &= ~0x80000000
    style |= 0x40000000
    ctypes.windll.user32.SetWindowLongW(overlay_hwnd, -16, ctypes.c_long(style))

    ex_style = ctypes.windll.user32.GetWindowLongW(overlay_hwnd, -20)
    ex_style |= 0x00080000 | 0x00000020 | 0x08000000
    ctypes.windll.user32.SetWindowLongW(overlay_hwnd, -20, ctypes.c_long(ex_style))

    ctypes.windll.user32.SetLayeredWindowAttributes(overlay_hwnd, 0, 0, 0x00000001)
    ctypes.windll.user32.SetWindowPos(overlay_hwnd, None, 0, 0, width, height, 0x0001 | 0x0020)
    return screen, overlay_hwnd, width, height

def update_overlay(overlay_hwnd, parent_hwnd):
    rect = wintypes.RECT()
    ctypes.windll.user32.GetClientRect(parent_hwnd, ctypes.byref(rect))
    w = rect.right - rect.left
    h = rect.bottom - rect.top
    ctypes.windll.user32.SetWindowPos(overlay_hwnd, None, 0, 0, w, h, 0x0001 | 0x0004 | 0x0020)
    return w, h

def draw_esp(screen, players, screen_w, screen_h, font):
    screen.fill((0, 0, 0))

    for p in players:
        feet = p['feet_screen']
        head = p['head_screen']
        if not feet or not head:
            continue
        fx, fy = feet
        hx, hy = head
        hp = p['hp']
        name = p['name']
        color = p['color']

        box_h = fy - hy
        box_w = box_h * 0.5
        box_x = fx - box_w / 2

        if config['box_style'] == 'full':
            pygame.draw.rect(screen, color, (box_x, hy, box_w, box_h), 2)
        elif config['box_style'] == 'corner':
            line_len = box_w * 0.3
            pygame.draw.line(screen, color, (box_x, hy), (box_x + line_len, hy), 2)
            pygame.draw.line(screen, color, (box_x, hy), (box_x, hy + line_len), 2)
            pygame.draw.line(screen, color, (box_x + box_w, hy), (box_x + box_w - line_len, hy), 2)
            pygame.draw.line(screen, color, (box_x + box_w, hy), (box_x + box_w, hy + line_len), 2)
            pygame.draw.line(screen, color, (box_x, fy), (box_x + line_len, fy), 2)
            pygame.draw.line(screen, color, (box_x, fy), (box_x, fy - line_len), 2)
            pygame.draw.line(screen, color, (box_x + box_w, fy), (box_x + box_w - line_len, fy), 2)
            pygame.draw.line(screen, color, (box_x + box_w, fy), (box_x + box_w, fy - line_len), 2)

        if config['health_bar'] == True:
            bar_x = box_x - 7
            bar_y = hy
            bar_h = box_h
            bar_w = 4
            fill_h = int(bar_h * hp / 100)
            pygame.draw.rect(screen, (60, 60, 60), (bar_x, bar_y, bar_w, bar_h))
            pygame.draw.rect(screen, (0, 255, 0), (bar_x, bar_y + bar_h - fill_h, bar_w, fill_h))

        if config['show_names']:
            txt = font.render(name, True, (255, 255, 255))
            screen.blit(txt, (box_x, hy - 16))

        tracer = config['tracer_type']
        if tracer == 'off':
            pass
        elif tracer == 'top':
            pygame.draw.line(screen, color, (screen_w // 2, 0), (fx, fy), 1)
        elif tracer == 'middle':
            pygame.draw.line(screen, color, (screen_w // 2, screen_h // 2), (fx, fy), 1)
        elif tracer == 'bottom':
            pygame.draw.line(screen, color, (screen_w // 2, screen_h), (fx, fy), 1)

def main():
    try:
        pm = pymem.Pymem("cs2.exe")
        client = pymem.process.module_from_name(pm.process_handle, "client.dll")
        client_base = client.lpBaseOfDll
    except:
        print("cs2.exe not running")
        return

    game_hwnd = get_game_window()
    if not game_hwnd:
        print("cs2 window not found")
        return

    entity_system = pm.read_ulonglong(client_base + dwGameEntitySystem)
    flat_array = pm.read_ulonglong(entity_system + EntityArrayOffset)

    chunk_ptrs = []
    for chunk_idx in range(2):
        ptr = pm.read_ulonglong(entity_system + 0x10 + chunk_idx * 8)
        chunk_ptrs.append(ptr if ptr and ptr >= 0x10000 else 0)

    screen, overlay_hwnd, cur_w, cur_h = init_overlay(game_hwnd)
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 16)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_END:
                running = False

        cur_w, cur_h = update_overlay(overlay_hwnd, game_hwnd)

        view_matrix = read_view_matrix(pm, client_base)
        local_team = get_local_team(pm, client_base)

        players = []
        for chunk_idx in range(2):
            chunk_ptr = chunk_ptrs[chunk_idx]
            if not chunk_ptr:
                continue

            for idx_in_chunk in range(512):
                i = chunk_idx * 512 + idx_in_chunk
                try:
                    controller = pm.read_ulonglong(chunk_ptr + idx_in_chunk * EntityStride)
                    if not controller or controller < 0x10000:
                        continue

                    pawn_handle = pm.read_int(controller + offsets["m_hPlayerPawn"])
                    if pawn_handle in (0, 0xFFFFFFFF, -0x80000000):
                        continue

                    pawn = 0
                    pawn_idx = pawn_handle & 0x7FFF
                    pawn_chunk_idx = pawn_idx >> 9
                    if pawn_chunk_idx < len(chunk_ptrs):
                        pawn_chunk_ptr = chunk_ptrs[pawn_chunk_idx]
                        if pawn_chunk_ptr:
                            pawn = pm.read_ulonglong(pawn_chunk_ptr + (pawn_idx & 0x1FF) * EntityStride)

                    if not pawn or pawn < 0x10000:
                        if 0 < pawn_idx < 4096:
                            pawn = pm.read_ulonglong(flat_array + pawn_idx * 8)
                            if pawn and pawn < 0x10000:
                                pawn = 0
                    if not pawn or pawn < 0x10000:
                        continue

                    hp = pm.read_int(pawn + offsets["m_iHealth"])
                    if hp <= 0 or hp > 100:
                        continue

                    team = get_team(pm, controller, pawn)
                    color = config['enemy_color'] if (local_team == 0 or team != local_team) else config['team_color']

                    x = pm.read_float(pawn + offsets["m_vOldOrigin"])
                    y = pm.read_float(pawn + offsets["m_vOldOrigin"] + 4)
                    z = pm.read_float(pawn + offsets["m_vOldOrigin"] + 8)
                    if x == 0.0 and y == 0.0 and z == 0.0:
                        continue

                    name = "Unknown"
                    if config['show_names']:
                        try:
                            name = pm.read_string(controller + offsets["m_iszPlayerName"], 32).strip()
                        except:
                            pass

                    feet_screen = world_to_screen(view_matrix, x, y, z, cur_w, cur_h)
                    head_screen = world_to_screen(view_matrix, x, y, z + 72, cur_w, cur_h)
                    if feet_screen and head_screen:
                        players.append({
                            'feet_screen': feet_screen,
                            'head_screen': head_screen,
                            'hp': hp,
                            'name': name,
                            'color': color,
                        })
                except:
                    continue

        draw_esp(screen, players, cur_w, cur_h, font)
        pygame.display.update()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()
