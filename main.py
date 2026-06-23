import base64
import requests
from datetime import datetime
import flet as ft
import os

# ========== 百度AI配置 ==========
BAIDU_API_KEY = "r3HGbOCsZDSuSwfvSdylVQzn"
BAIDU_SECRET_KEY = "BRXV1rCWGTqFeKkyAhzuHegvbD7Dl8qs"


def get_baidu_access_token():
    url = (f"https://aip.baidubce.com/oauth/2.0/token"
           f"?grant_type=client_credentials"
           f"&client_id={BAIDU_API_KEY}"
           f"&client_secret={BAIDU_SECRET_KEY}")
    try:
        response = requests.post(url, timeout=10)
        if response.status_code == 200:
            return response.json().get("access_token")
        return None
    except Exception:
        return None


def baidu_document_analysis(image_base64):
    access_token = get_baidu_access_token()
    if not access_token:
        return {"error": "无法获取API令牌"}
    url = f"https://aip.baidubce.com/rest/2.0/ocr/v1/general_basic?access_token={access_token}"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {"image": image_base64, "language_type": "CHN_ENG", "detect_direction": "true"}
    try:
        response = requests.post(url, headers=headers, data=data, timeout=30)
        return response.json()
    except Exception as e:
        return {"error": str(e)}


# ========== 数据 ==========
MINDMAP_DATA = {
    "智能文档解析APP": {
        "children": {
            "📱 身份认证": {"children": {"🔐 登录": {}, "📝 注册": {}, "🔑 密码找回": {}, "👤 个人中心": {}}},
            "📷 OCR识别": {"children": {"📄 通用识别": {}, "🎯 高精度识别": {}, "📊 表格识别": {}, "🌐 多语言识别": {}}},
            "🧠 AI能力": {"children": {"🤖 百度OCR API": {}, "📈 识别准确率90%+": {}, "⚡ 实时识别": {}, "📱 多格式支持": {}}},
            "📊 历史记录": {"children": {"📋 识别记录": {}, "📈 统计图表": {}, "🗑️ 清除记录": {}}},
            "⚙️ 设置": {"children": {"🌓 主题切换": {}, "🔔 通知设置": {}, "📖 使用帮助": {}, "ℹ️ 关于我们": {}}}
        }
    }
}

users_db = {"admin": {"password": "123456", "nickname": "管理员"}}
parse_history = []

# ========== 颜色 ==========
BLUE = "#1565C0"
GREEN = "#43A047"
ORANGE = "#E65100"
PURPLE = "#6A1B9A"
GREY_50 = "#FAFAFA"
GREY_100 = "#F5F5F5"
GREY_200 = "#EEEEEE"
GREY_300 = "#E0E0E0"
GREY_400 = "#BDBDBD"
GREY_500 = "#9E9E9E"
GREY_600 = "#757575"
WHITE = "#FFFFFF"
RED = "#F44336"

# ========== 全局状态 ==========
app = {
    "page": None,
    "user": None,
    "container": None,
    "mode": "通用识别",
    "image_data": None,
    "file_name": None,
    "result_text": None,
    "result_display": None,
    "image_display": None,
    "home": None,
    "parse": None,
    "history": None,
    "profile": None,
    "settings": None,
    "nav_buttons": [],
    "nav_icons": [],
    "nav_labels": [],
}


def show_mindmap_dialog(page):
    def build_node(title, children=None, level=0):
        children = children or {}
        colors = [BLUE, "#0097A7", GREEN, ORANGE]
        bg = ["#E3F2FD", "#E0F7FA", "#E8F5E9", "#FFF3E0"]
        idx = min(level, len(colors) - 1)
        is_leaf = not bool(children)

        child_container = ft.Column(spacing=1, visible=False)

        for child_title, child_data in children.items():
            child_container.controls.append(
                build_node(child_title, child_data.get("children", {}), level + 1)
            )

        def toggle(e):
            child_container.visible = not child_container.visible
            e.control.update()
            child_container.update()

        return ft.Column([
            ft.Container(
                content=ft.Row([
                    ft.Text("📁" if not is_leaf else "📄", size=16),
                    ft.Text(title, size=14 if level < 2 else 12,
                            weight=ft.FontWeight.BOLD if level < 1 else ft.FontWeight.NORMAL),
                    ft.Text("▶" if not is_leaf else "", size=14, color=GREY_500),
                ], spacing=8),
                padding=ft.padding.symmetric(horizontal=12, vertical=6),
                bgcolor=bg[idx],
                border_radius=6,
                ink=True,
                on_click=toggle if not is_leaf else None,
            ),
            ft.Container(child_container, padding=ft.padding.only(left=20 + level * 10)),
        ], spacing=1)

    tree = build_node("🚀 智能文档解析APP", MINDMAP_DATA["智能文档解析APP"]["children"])
    dialog = ft.AlertDialog(
        title=ft.Text("📋 功能思维导图", size=18, weight=ft.FontWeight.BOLD),
        content=ft.Container(
            content=ft.Column([
                ft.Text("点击节点展开/收起", size=12, color=GREY_500),
                ft.Container(
                    content=ft.Column(controls=[tree], scroll=ft.ScrollMode.AUTO, height=380),
                    width=340,
                )
            ], spacing=8),
            width=360, height=430
        ),
        actions=[ft.TextButton("关闭", on_click=lambda e: setattr(dialog, 'open', False) or page.update())],
    )
    page.dialog = dialog
    dialog.open = True
    page.update()


def refresh_all_pages(page):
    if app["home"]:
        app["home"] = home_page(page)
    if app["history"]:
        app["history"] = history_page(page)
    if app["profile"]:
        app["profile"] = profile_page(page)
    if app["container"]:
        current = app["container"].content
        if current == app["home"]:
            app["container"].content = app["home"]
        elif current == app["history"]:
            app["container"].content = app["history"]
        elif current == app["profile"]:
            app["container"].content = app["profile"]
        page.update()


def home_page(page):
    def go_parse(e):
        switch_tab(page, 1)
    def go_history(e):
        switch_tab(page, 2)
    def go_profile(e):
        switch_tab(page, 3)
    def go_settings(e):
        switch_tab(page, 4)

    total_count = len(parse_history)
    total_words = sum(h.get("count", 0) for h in parse_history)
    last = parse_history[-1] if parse_history else None

    return ft.Container(
        content=ft.Column([
            ft.Container(height=10),
            ft.Text(f"👋 你好, {app['user']}!", size=24, weight=ft.FontWeight.BOLD),
            ft.Text("欢迎使用智能文档解析系统", size=14, color=GREY_600),
            ft.Divider(height=16),
            ft.Row([
                _stat_card("📄", "解析次数", str(total_count), BLUE),
                _stat_card("📝", "提取字数", str(total_words), GREEN),
                _stat_card("📊", "支持格式", "图片", ORANGE),
            ], alignment=ft.MainAxisAlignment.SPACE_EVENLY),
            ft.Divider(height=12),
            ft.Text("⚡ 快捷入口", size=16, weight=ft.FontWeight.BOLD),
            ft.Row([
                _card("📷", "OCR识别", BLUE, go_parse),
                _card("🧠", "思维导图", PURPLE, lambda e: show_mindmap_dialog(page)),
                _card("📊", "历史记录", GREEN, go_history),
                _card("⚙️", "设置", ORANGE, go_settings),
            ], alignment=ft.MainAxisAlignment.SPACE_EVENLY),
            ft.Divider(height=12),
            ft.Text("📋 最近识别", size=16, weight=ft.FontWeight.BOLD),
            ft.Container(
                content=ft.Column([
                    ft.Text(f"🕐 {last['time']}", size=12, color=GREY_600) if last else ft.Text("暂无记录"),
                    ft.Text(f"📄 {last['type']} | {last['count']} 个字" if last else "去OCR页面试试吧！", size=13),
                ], spacing=4),
                padding=ft.padding.all(12), bgcolor=WHITE, border_radius=8
            ) if last else ft.Text("暂无识别记录", color=GREY_400),
            ft.Container(
                content=ft.Column([
                    ft.Text("🚀 核心功能", size=16, weight=ft.FontWeight.BOLD),
                    ft.Text("• 通用/高精度OCR文字识别", size=13),
                    ft.Text("• 基于百度AI PaddleOCR", size=13),
                    ft.Text("• 识别准确率90%以上", size=13),
                    ft.Text("• 支持 PNG / JPG / BMP 图片", size=13),
                ], spacing=4),
                padding=ft.padding.all(12), bgcolor=WHITE, border_radius=8
            ),
        ], spacing=6),
        padding=16, expand=True, bgcolor=GREY_50
    )


def _stat_card(icon, label, value, color):
    return ft.Container(
        content=ft.Column([
            ft.Text(icon, size=20),
            ft.Text(value, size=18, weight=ft.FontWeight.BOLD, color=color),
            ft.Text(label, size=10, color=GREY_500),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
        padding=ft.padding.symmetric(horizontal=12, vertical=6),
        bgcolor=WHITE, border_radius=8, width=90,
    )


def _card(icon, title, color, on_click):
    return ft.Container(
        content=ft.Column([
            ft.Text(icon, size=28),
            ft.Text(title, size=12, weight=ft.FontWeight.BOLD)
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4),
        padding=ft.padding.all(10), width=75, height=80,
        bgcolor=WHITE, border_radius=10,
        ink=True, on_click=on_click
    )


# ========== OCR页面 ==========
def parse_page(page):
    app["image_display"] = ft.Container(
        content=ft.Column([
            ft.Text("🖼", size=50),
            ft.Text("上传图片进行识别", size=12, color=GREY_500),
            ft.Text("支持 PNG / JPG / BMP", size=10, color=GREY_400),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4),
        width=340, height=160, bgcolor=GREY_100, border_radius=12
    )

    app["result_text"] = ft.Text("识别结果将显示在这里...", size=13, color=GREY_600)
    app["result_display"] = ft.Container(
        content=ft.Column([
            ft.Text("📝 识别结果", size=14, weight=ft.FontWeight.BOLD),
            ft.Divider(height=2),
            ft.Container(
                content=app["result_text"],
                padding=10,
            )
        ], spacing=4, scroll=ft.ScrollMode.AUTO),
        padding=12,
        bgcolor=WHITE,
        border_radius=8,
        height=250,
        width=340,
    )

    mode_text = ft.Text("当前: 通用识别", size=14)
    mode_value = "通用"

    def toggle_mode(e):
        nonlocal mode_value
        mode_value = "高精度" if mode_value == "通用" else "通用"
        mode_text.value = f"当前: {mode_value}识别"
        page.update()

    def pick_image(e):
        def on_result(e):
            if e.files:
                try:
                    file_path = e.files[0].path
                    file_name = e.files[0].name
                    file_ext = os.path.splitext(file_name)[1].lower()

                    app["file_name"] = file_name

                    if file_ext in ['.png', '.jpg', '.jpeg', '.bmp']:
                        with open(file_path, "rb") as f:
                            app["image_data"] = base64.b64encode(f.read()).decode()
                        app["image_display"].content = ft.Column([
                            ft.Text("✅", size=50),
                            ft.Text(f"已选择: {file_name}", size=12, color=GREEN),
                            ft.Text("点击开始识别", size=11, color=GREY_500)
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4)
                        app["result_text"].value = f"📷 图片已加载: {file_name}"
                        page.update()
                    else:
                        app["result_text"].value = f"❌ 不支持的文件格式: {file_ext}"
                        page.update()
                except Exception as ex:
                    app["result_text"].value = f"❌ 加载失败: {str(ex)}"
                    page.update()

        picker = ft.FilePicker(on_result=on_result)
        page.overlay.append(picker)
        page.update()
        picker.pick_files(
            allowed_extensions=["png", "jpg", "jpeg", "bmp"],
            dialog_title="选择图片",
        )

    def start_parse(e):
        nonlocal mode_value
        if not app["image_data"]:
            app["result_text"].value = "⚠️ 请先上传图片"
            page.update()
            return

        app["result_text"].value = "⏳ 正在识别中..."
        page.update()

        # 调用百度API
        if mode_value == "高精度":
            result = baidu_document_analysis(app["image_data"])
        else:
            result = baidu_document_analysis(app["image_data"])

        if "error" in result:
            app["result_text"].value = f"❌ 识别失败: {result['error']}"
            page.update()
            return

        words = [w["words"] for w in result.get("words_result", [])]
        if not words:
            app["result_text"].value = "⚠️ 未识别到文字"
            page.update()
            return

        result_text = "\n".join(words)
        count = len(words)
        type_name = f"{mode_value}识别"

        app["result_text"].value = f"✅ 识别成功! ({count}个字)\n\n{result_text}"
        page.update()

        parse_history.append({
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "user": app["user"],
            "type": type_name,
            "text": result_text[:80] + ("..." if len(result_text) > 80 else ""),
            "count": count,
            "file": app.get("file_name", "未知文件")
        })

        refresh_all_pages(page)

    return ft.Column([
        ft.Container(
            content=ft.Row([
                ft.Text("📷 OCR识别", size=18, weight=ft.FontWeight.BOLD, color=WHITE)
            ]),
            padding=ft.padding.symmetric(horizontal=16, vertical=12),
            bgcolor=BLUE
        ),
        ft.Container(
            content=ft.Column([
                ft.Row([
                    mode_text,
                    ft.ElevatedButton("切换模式", on_click=toggle_mode,
                                    style=ft.ButtonStyle(bgcolor=PURPLE, color=WHITE))
                ], spacing=10),
                ft.Text("通用模式: 速度快 / 高精度模式: 更准确", size=11, color=GREY_500),
                ft.Divider(height=4),
                app["image_display"],
                ft.Row([
                    ft.ElevatedButton("📁 选择图片", on_click=pick_image),
                    ft.ElevatedButton("🚀 开始识别", on_click=start_parse,
                                     style=ft.ButtonStyle(bgcolor=GREEN, color=WHITE))
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=12),
                ft.Divider(height=4),
                app["result_display"],
            ], spacing=8),
            padding=16, expand=True, bgcolor=GREY_50
        )
    ], spacing=0, expand=True)


# ========== 历史页面 ==========
def history_page(page):
    def clear_all(e):
        def confirm(e):
            if e.control.text == "确认":
                parse_history.clear()
                app["history"] = history_page(page)
                app["container"].content = app["history"]
                page.update()
            dialog.open = False
            page.update()

        dialog = ft.AlertDialog(
            title=ft.Text("⚠️ 确认清除"),
            content=ft.Text("确定删除所有历史记录吗？"),
            actions=[
                ft.TextButton("取消", on_click=lambda e: setattr(dialog, 'open', False) or page.update()),
                ft.ElevatedButton("确认", on_click=confirm, style=ft.ButtonStyle(bgcolor=RED))
            ]
        )
        page.dialog = dialog
        dialog.open = True
        page.update()

    total = len(parse_history)
    words = sum(h.get("count", 0) for h in parse_history)
    user_parses = [h for h in parse_history if h.get("user") == app["user"]]

    stats = ft.Row([
        ft.Container(
            content=ft.Column([ft.Text(str(total), size=20, weight=ft.FontWeight.BOLD, color=BLUE),
                              ft.Text("总识别", size=11, color=GREY_500)]),
            padding=16, bgcolor=WHITE, border_radius=8, width=80, alignment=ft.alignment.center
        ),
        ft.Container(
            content=ft.Column([ft.Text(str(words), size=20, weight=ft.FontWeight.BOLD, color=GREEN),
                              ft.Text("总字数", size=11, color=GREY_500)]),
            padding=16, bgcolor=WHITE, border_radius=8, width=80, alignment=ft.alignment.center
        ),
        ft.Container(
            content=ft.Column([ft.Text(str(len(user_parses)), size=20, weight=ft.FontWeight.BOLD, color=ORANGE),
                              ft.Text("我的识别", size=11, color=GREY_500)]),
            padding=16, bgcolor=WHITE, border_radius=8, width=80, alignment=ft.alignment.center
        ),
    ], alignment=ft.MainAxisAlignment.SPACE_EVENLY)

    if parse_history:
        items = []
        for h in reversed(parse_history[-30:]):
            items.append(ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Text(f"🕐 {h['time']}", size=11, color=GREY_600),
                        ft.Container(ft.Text(h['type'], size=10, color=WHITE),
                                   padding=ft.padding.symmetric(horizontal=8, vertical=2),
                                   bgcolor=BLUE, border_radius=8)
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Text(f"📄 {h.get('file', '')} | {h['text']}", size=13),
                    ft.Text(f"字数: {h['count']} | 用户: {h.get('user', '')}", size=11, color=GREY_500)
                ], spacing=4),
                padding=10, bgcolor=WHITE, border_radius=8, margin=ft.margin.symmetric(vertical=3)
            ))
        list_view = ft.Column(controls=items, scroll=ft.ScrollMode.AUTO, height=400)
    else:
        list_view = ft.Container(
            content=ft.Column([
                ft.Text("📭", size=60),
                ft.Text("暂无识别记录", size=16, color=GREY_400)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            expand=True, alignment=ft.alignment.center
        )

    return ft.Column([
        ft.Container(
            content=ft.Row([
                ft.Text("📊 识别历史", size=18, weight=ft.FontWeight.BOLD, color=WHITE),
                ft.Container(expand=True),
                ft.TextButton("🗑 清除", on_click=clear_all, style=ft.ButtonStyle(color=WHITE))
            ]),
            padding=ft.padding.symmetric(horizontal=16, vertical=12),
            bgcolor=BLUE
        ),
        ft.Container(
            content=ft.Column([stats, ft.Divider(height=4), list_view], spacing=8),
            padding=16, expand=True, bgcolor=GREY_50
        )
    ], spacing=0, expand=True)


# ========== 设置页面 ==========
def settings_page(page):
    theme_mode = ft.Text("🌓 主题模式: 浅色", size=14)

    def toggle_theme(e):
        if page.theme_mode == "light":
            page.theme_mode = "dark"
            theme_mode.value = "🌓 主题模式: 深色"
        else:
            page.theme_mode = "light"
            theme_mode.value = "🌓 主题模式: 浅色"
        page.update()

    def about(e):
        dialog = ft.AlertDialog(
            title=ft.Text("ℹ️ 关于"),
            content=ft.Column([
                ft.Text("智能文档解析APP", size=16, weight=ft.FontWeight.BOLD),
                ft.Text("基于百度AI PaddleOCR", size=13, color=GREY_600),
                ft.Text("版本 1.0", size=12, color=GREY_500),
                ft.Text("智能交互技术 大作业", size=12, color=GREY_500),
                ft.Text("支持 PNG / JPG / BMP", size=12, color=GREY_500),
            ], spacing=4, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            actions=[ft.TextButton("关闭", on_click=lambda e: setattr(dialog, 'open', False) or page.update())],
        )
        page.dialog = dialog
        dialog.open = True
        page.update()

    return ft.Column([
        ft.Container(
            content=ft.Row([
                ft.Text("⚙️ 设置", size=18, weight=ft.FontWeight.BOLD, color=WHITE)
            ]),
            padding=ft.padding.symmetric(horizontal=16, vertical=12),
            bgcolor=BLUE
        ),
        ft.Container(
            content=ft.Column([
                ft.Container(
                    content=ft.Column([
                        theme_mode,
                        ft.ElevatedButton("切换主题", on_click=toggle_theme, width=150),
                    ], spacing=8),
                    padding=16, bgcolor=WHITE, border_radius=8
                ),
                ft.Container(
                    content=ft.Column([
                        ft.Text("📖 使用帮助", size=14, weight=ft.FontWeight.BOLD),
                        ft.Text("支持格式: PNG, JPG, BMP", size=12, color=GREY_600),
                        ft.Text("1. 选择图片 2. 切换模式 3. 开始识别", size=12, color=GREY_600),
                    ], spacing=4),
                    padding=16, bgcolor=WHITE, border_radius=8, ink=True,
                ),
                ft.Container(
                    content=ft.Column([
                        ft.Text("ℹ️ 关于我们", size=14, weight=ft.FontWeight.BOLD),
                        ft.Text("版本信息与联系方式", size=12, color=GREY_600),
                    ], spacing=4),
                    padding=16, bgcolor=WHITE, border_radius=8, ink=True,
                    on_click=about
                ),
            ], spacing=8),
            padding=16, expand=True, bgcolor=GREY_50
        )
    ], spacing=0, expand=True)


# ========== 个人中心 ==========
def profile_page(page):
    def logout(e):
        app["user"] = None
        page.controls.clear()
        login_page(page)
        page.update()

    info = users_db.get(app["user"], {})
    user_parses = [h for h in parse_history if h.get("user") == app["user"]]
    count = len(user_parses)
    total_words = sum(h.get("count", 0) for h in user_parses)

    return ft.Column([
        ft.Container(
            content=ft.Row([
                ft.Text("👤 个人中心", size=18, weight=ft.FontWeight.BOLD, color=WHITE)
            ]),
            padding=ft.padding.symmetric(horizontal=16, vertical=12),
            bgcolor=BLUE
        ),
        ft.Container(
            content=ft.Column([
                ft.Container(
                    content=ft.Column([
                        ft.CircleAvatar(
                            content=ft.Text(app["user"][0].upper(), size=32, color=WHITE),
                            bgcolor=BLUE, radius=45
                        ),
                        ft.Text(f"👤 {app['user']}", size=22, weight=ft.FontWeight.BOLD),
                        ft.Text(f"昵称: {info.get('nickname', '未设置')}", size=14, color=GREY_600),
                        ft.Text(f"📷 识别次数: {count} 次", size=13, color=GREY_600),
                        ft.Text(f"📝 识别字数: {total_words} 个", size=13, color=GREY_600),
                        ft.Text(f"账号类型: {'管理员' if app['user'] == 'admin' else '普通用户'}", size=13, color=GREY_600),
                        ft.Divider(height=12),
                        ft.ElevatedButton("🚪 退出登录", on_click=logout,
                                        style=ft.ButtonStyle(bgcolor=RED, color=WHITE), width=200)
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6),
                    padding=30, bgcolor=WHITE, border_radius=12
                )
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=16, expand=True, bgcolor=GREY_50
        )
    ], spacing=0, expand=True)


# ========== 登录页面 ==========
def login_page(page):
    is_register = False
    username = ft.TextField(hint_text="用户名", width=280)
    password = ft.TextField(hint_text="密码", password=True, width=280)
    confirm = ft.TextField(hint_text="确认密码", password=True, width=280, visible=False)
    error = ft.Text("", color="red", size=13)

    def toggle(e):
        nonlocal is_register
        is_register = not is_register
        confirm.visible = is_register
        login_btn.text = "注册" if is_register else "登录"
        toggle_btn.text = "已有账号？去登录" if is_register else "注册新账号"
        error.value = ""
        page.update()

    def do_action(e):
        nonlocal is_register
        name = username.value.strip()
        pwd = password.value

        if not name or not pwd:
            error.value = "请填写完整信息"
            page.update()
            return

        if is_register:
            if pwd != confirm.value:
                error.value = "两次密码不一致"
                page.update()
                return
            if name in users_db:
                error.value = "用户名已存在"
                page.update()
                return
            users_db[name] = {"password": pwd, "nickname": name}
            error.value = "✅ 注册成功！请登录"
            error.color = GREEN
            page.update()
            is_register = False
            confirm.visible = False
            login_btn.text = "登录"
            toggle_btn.text = "注册新账号"
            password.value = ""
            confirm.value = ""
            error.color = "red"
            page.update()
        else:
            if name in users_db and users_db[name]["password"] == pwd:
                app["user"] = name
                page.controls.clear()
                main_page_view(page)
                page.update()
            else:
                error.value = "用户名或密码错误"
                page.update()

    login_btn = ft.ElevatedButton("登录", on_click=do_action, width=280)
    toggle_btn = ft.TextButton("注册新账号", on_click=toggle)

    page.add(
        ft.Container(
            content=ft.Column([
                ft.Container(height=40),
                ft.Text("📄", size=64),
                ft.Text("智能文档解析", size=30, weight=ft.FontWeight.BOLD, color=BLUE),
                ft.Text("基于百度AI · PaddleOCR", size=14, color=GREY_500),
                ft.Container(height=30),
                username, password, confirm,
                error,
                login_btn,
                toggle_btn,
                ft.Container(expand=True),
                ft.Text("© 2026 智能交互大作业", size=11, color=GREY_400)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8),
            padding=30, expand=True, alignment=ft.alignment.center
        )
    )


def switch_tab(page, index):
    tabs = [app["home"], app["parse"], app["history"], app["profile"], app["settings"]]
    app["container"].content = tabs[index]
    for i, btn in enumerate(app["nav_buttons"]):
        if i == index:
            btn.content = ft.Column([
                ft.Text(app["nav_icons"][i], size=18),
                ft.Text(app["nav_labels"][i], size=9, color=BLUE, weight=ft.FontWeight.BOLD)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0)
        else:
            btn.content = ft.Column([
                ft.Text(app["nav_icons"][i], size=18),
                ft.Text(app["nav_labels"][i], size=9, color=GREY_500)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0)
    page.update()


def main_page_view(page):
    app["home"] = home_page(page)
    app["parse"] = parse_page(page)
    app["history"] = history_page(page)
    app["profile"] = profile_page(page)
    app["settings"] = settings_page(page)

    app["nav_icons"] = ["🏠", "📷", "📊", "👤", "⚙️"]
    app["nav_labels"] = ["首页", "OCR", "历史", "我的", "设置"]

    def make_nav_btn(index, icon, label, active=False):
        return ft.Container(
            content=ft.Column([
                ft.Text(icon, size=18),
                ft.Text(label, size=9, color=BLUE if active else GREY_500,
                       weight=ft.FontWeight.BOLD if active else ft.FontWeight.NORMAL)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0),
            padding=ft.padding.symmetric(horizontal=8, vertical=4),
            ink=True, on_click=lambda e, i=index: switch_tab(page, i),
            expand=True,
        )

    app["nav_buttons"] = [
        make_nav_btn(0, "🏠", "首页", True),
        make_nav_btn(1, "📷", "OCR"),
        make_nav_btn(2, "📊", "历史"),
        make_nav_btn(3, "👤", "我的"),
        make_nav_btn(4, "⚙️", "设置"),
    ]

    nav_bar = ft.Container(
        content=ft.Row(app["nav_buttons"], spacing=0),
        padding=ft.padding.symmetric(vertical=4),
        bgcolor=WHITE,
        border=ft.border.only(top=ft.border.BorderSide(1, GREY_200)),
    )

    app["container"] = ft.Container(content=app["home"], expand=True)

    page.add(ft.Column([app["container"], nav_bar], spacing=0, expand=True))


def main(page: ft.Page):
    app["page"] = page
    page.title = "智能文档解析APP"
    page.theme_mode = "light"
    page.bgcolor = GREY_50
    page.padding = 0
    page.window.width = 400
    page.window.height = 780
    page.window.resizable = True
    login_page(page)


if __name__ == "__main__":
    ft.app(target=main)"# ���´��" 
