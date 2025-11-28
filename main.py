import logging
import asyncio
import sys
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    InlineKeyboardMarkup, 
    InlineKeyboardButton, 
    ReplyKeyboardMarkup, 
    KeyboardButton, 
    BufferedInputFile
)
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest

import config
import database
from services import ssh_manager

logging.basicConfig(level=logging.INFO, stream=sys.stdout)

bot = Bot(token=config.TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
router = Router()

class ServerForm(StatesGroup):
    ip = State()
    port = State()
    username = State()
    password = State()

class PanelState(StatesGroup):
    selected_server_id = State() 

class CreateUserForm(StatesGroup):
    username = State()
    traffic = State()
    days = State()

class EditUserForm(StatesGroup):
    select_user = State()
    new_traffic = State()
    new_days = State()

def get_main_keyboard():
    kb = [
        [KeyboardButton(text="☁️ VPS GOŞ / AÝYR")],
        [KeyboardButton(text="⚙️ Panel"), KeyboardButton(text="🗑 OpenVPN Poz")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, input_field_placeholder="Bir işlem saýlaň...")

def get_panel_menu():
    buttons = [
        [
            InlineKeyboardButton(text="👤 Ulanyjy Döret", callback_data="panel_create"),
            InlineKeyboardButton(text="🟢 Aktifler", callback_data="panel_online")
        ],
        [
            InlineKeyboardButton(text="🗑 Ulanyjy Poz", callback_data="panel_delete"),
            InlineKeyboardButton(text="✏️ Ulanyjylar (Düzelt)", callback_data="panel_list")
        ],
        [InlineKeyboardButton(text="❌ Paneli Ýap", callback_data="close_panel")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_cancel_btn():
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Ýatyr", callback_data="cancel_action")]])

async def safe_edit(call: types.CallbackQuery, text: str, reply_markup=None):
    try:
        await call.message.edit_text(text, reply_markup=reply_markup)
    except TelegramBadRequest:
        await call.message.delete()
        await call.message.answer(text, reply_markup=reply_markup)

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "<b>👋 Salam! SkyLyne Multi-Server Manager!</b>\n\n"
        "Professional VPN dolandyryjy.\n"
        "Başlamak üçin aşakdaky düwmeleri ulanyň.", 
        reply_markup=get_main_keyboard()
    )

@router.message(F.text == "☁️ VPS GOŞ / AÝYR")
async def kbd_manage_vps(message: types.Message):
    servers = database.get_user_servers(message.chat.id)
    
    buttons = []
    for s in servers:
        buttons.append([InlineKeyboardButton(text=f"🗑 Poz: {s['user']}@{s['ip']}:{s['port']}", callback_data=f"delete_vps_{s['id']}")])
    
    buttons.append([InlineKeyboardButton(text="➕ Taze VPS Goş", callback_data="start_add_vps")])
    
    await message.answer("<b>🖥 VPS dolandyryş</b>\n\nPozmak isleýän VPS-iňizi saýlaň ýa-da täzesini goşuň:", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

@router.callback_query(F.data == "start_add_vps")
async def cb_start_add_vps(call: types.CallbackQuery, state: FSMContext):
    await state.set_state(ServerForm.ip)
    await safe_edit(call, "🖥 <b>Täze VPS IP adresini yaz:</b>", reply_markup=get_cancel_btn())

@router.callback_query(F.data.startswith("delete_vps_"))
async def cb_delete_vps(call: types.CallbackQuery):
    server_id = int(call.data.split("_")[2])
    database.delete_server(server_id)
    await call.answer("VPS pozuldy!", show_alert=True)
    await safe_edit(call, "✅ VPS we oňa degişli ähli ulanyjylar pozuldy.")

@router.message(ServerForm.ip)
async def flow_ip(message: types.Message, state: FSMContext):
    await state.update_data(ip=message.text)
    await state.set_state(ServerForm.port)
    await message.answer("🔌 <b>SSH Portuny ýazyň:</b>\n(Adatça: 22)", reply_markup=get_cancel_btn())

@router.message(ServerForm.port)
async def flow_port(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("⚠️ Port diňe san bolmaly (Mysal: 22).")
        return
    
    await state.update_data(port=int(message.text))
    await state.set_state(ServerForm.username)
    await message.answer("👤 <b>SSH Ulanyjy adyny ýazyň:</b>\n(Adatça: root)", reply_markup=get_cancel_btn())

@router.message(ServerForm.username)
async def flow_user(message: types.Message, state: FSMContext):
    await state.update_data(username=message.text)
    await state.set_state(ServerForm.password)
    await message.answer("🔑 <b>SSH Parolyny ýazyň:</b>", reply_markup=get_cancel_btn())

@router.message(ServerForm.password)
async def flow_pass(message: types.Message, state: FSMContext):
    data = await state.get_data()
    ip = data['ip']
    port = data['port']
    username = data['username']
    password = message.text
    new_id = database.add_server(message.chat.id, ip, port, username, password)
    await state.clear()
    
    msg = await message.answer(f"✅ <b>VPS ({username}@{ip}:{port}) goşuldy!</b>\n🔄 <i>OpenVPN gurnalýar... (az sabyr et)</i>")
    
    vps = database.get_server_by_id(new_id)
    success, logs = await ssh_manager.install_async(vps)
    
    if success:
        await msg.edit_text(f"🎉 <b>VPS ({ip}) tayar!</b>\nOka öwren döret.")
    else:

        print(f" (VPS INSTALL) - IP: {ip} - Log: {logs}")
        await msg.edit_text("❌ <b>Yalnyşlyk admine habar ber.</b>")

@router.message(F.text == "⚙️ Panel")
async def kbd_panel_select(message: types.Message):
    servers = database.get_user_servers(message.chat.id)
    if not servers:
        await message.answer("⚠️ <b>Vps ýok.</b>\nIlki '☁️ VPS GOŞ' düwmesine bas.")
        return
    
    buttons = []
    for s in servers:

        buttons.append([InlineKeyboardButton(text=f"🖥 {s['user']}@{s['ip']}", callback_data=f"select_vps_{s['id']}")])
    
    await message.answer("⚙️ <b>Haýsy vps paneli gerek saýla:</b>", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

@router.callback_query(F.data.startswith("select_vps_"))
async def cb_select_vps(call: types.CallbackQuery, state: FSMContext):
    server_id = int(call.data.split("_")[2])
    vps = database.get_server_by_id(server_id)
    
    if not vps:
        await call.answer("Bu serveri pozduna (b12 al).", show_alert=True)
        return

    await state.update_data(selected_server_id=server_id)
    await safe_edit(call, f"🌌 <b>Panel: {vps['ip']}</b>\nSaýla birzat?", reply_markup=get_panel_menu())

@router.callback_query(F.data == "close_panel")
async def cb_close(call: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.delete()
    await call.message.answer("Yapyldy.", reply_markup=get_main_keyboard())

@router.callback_query(F.data == "cancel_action")
async def cb_cancel(call: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.delete()
    await call.message.answer("Goybolsun edildi.", reply_markup=get_main_keyboard())

async def get_current_vps(state: FSMContext, call_msg):
    data = await state.get_data()
    server_id = data.get("selected_server_id")
    if not server_id:
        await call_msg.answer("⚠️ Tazeden synanş")
        return None
    return database.get_server_by_id(server_id)

@router.callback_query(F.data == "panel_create")
async def panel_create(call: types.CallbackQuery, state: FSMContext):
    await state.set_state(CreateUserForm.username)
    await safe_edit(call, "👤 <b>Ulanyjy ady näme bolsun?</b>", reply_markup=get_cancel_btn())

@router.message(CreateUserForm.username)
async def step_user(message: types.Message, state: FSMContext):
    raw_username = message.text
    safe_username = raw_username.replace(" ", "").strip()
    
    if not safe_username:
         await message.answer("Ulanyjy ady boş bolup bilmez.")
         return

    await state.update_data(username=safe_username)
    await state.set_state(CreateUserForm.traffic)
    await message.answer(f"👤 <b>{safe_username}</b> üçin traffik çägi näçe? (10GB, TB, MB, 0 - çaksiz diymekdir bul)", reply_markup=get_cancel_btn())

@router.message(CreateUserForm.traffic)
async def step_traffic(message: types.Message, state: FSMContext):
    await state.update_data(traffic=message.text)
    await state.set_state(CreateUserForm.days)
    await message.answer("📅 <b>Gün sany?</b> (30)", reply_markup=get_cancel_btn())

@router.message(CreateUserForm.days)
async def step_days(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("San yaz öw!")
        return
    days = int(message.text)
    data = await state.get_data()
    username = data['username']
    traffic = data['traffic']
    
    vps = await get_current_vps(state, message)
    if not vps: return

    server_id = data['selected_server_id']
    
    wait = await message.answer("⏳")
    
    success, msg, content = await ssh_manager.add_user_async(vps, username, traffic)
    
    if success:
        database.add_vpn_user(message.chat.id, server_id, username, traffic, days)
        await wait.delete()
        file = BufferedInputFile(content.encode(), filename=f"{username}.ovpn")
        await message.answer_document(file, caption=f"✅ <b>{username}</b> döredildi!\nIP: {vps['ip']}")
        await message.answer("Panel:", reply_markup=get_panel_menu())
    else:
        print(f"yalnyşlyk (USER CREATE) - Username: {username} - Msg: {msg}")
        await wait.edit_text("❌ <b>Yalnyşlyk admine habar ber.</b>")

@router.callback_query(F.data == "panel_online")
async def panel_online(call: types.CallbackQuery, state: FSMContext):
    vps = await get_current_vps(state, call.message)
    if not vps: return
    
    await call.answer("loading..")
    success, users = await ssh_manager.get_online_users_async(vps)
    
    if success and users:
        text = f"🟢 <b>Aktivler ({vps['ip']}):</b>\n\n"
        for u in users:
            text += f"👤 {u['user']} | {u['ip']} | {u['time']}\n"
    elif success and not users:
        text = "🟢 Hiç kim yok ya işlanok öytyan test edilmedik bul."
    else:
        print(f" (ONLINE CHECK) - Log: {users}")
        text = "❌ <b>Yalnyşlyk admine habar ber.</b>"
        
    await safe_edit(call, text, reply_markup=get_panel_menu())

@router.callback_query(F.data == "panel_delete")
async def panel_delete_menu(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    server_id = data.get("selected_server_id")
    users = database.get_vpn_users(server_id)
    
    if not users:
        await call.answer("Ulanyan yok!", show_alert=True)
        return
        
    btns = []
    for u in users:
        btns.append([InlineKeyboardButton(text=f"🗑 {u[1]}", callback_data=f"del_user_{u[1]}")])
    btns.append([InlineKeyboardButton(text="🔙 Yza", callback_data="back_to_panel")])
    
    await safe_edit(call, "Pozuljak ulanyjyny saylan:", reply_markup=InlineKeyboardMarkup(inline_keyboard=btns))

@router.callback_query(F.data.startswith("del_user_"))
async def process_del_user(call: types.CallbackQuery, state: FSMContext):
    username = call.data.split("_")[2]
    vps = await get_current_vps(state, call.message)
    data = await state.get_data()
    server_id = data['selected_server_id']
    
    await safe_edit(call, f"⏳ {username} pozulya")
    
    success, msg = await ssh_manager.revoke_user_async(vps, username)
    if success:
        database.delete_vpn_user(server_id, username)
        await safe_edit(call, f"✅ {username} pozuldy.", reply_markup=get_panel_menu())
    else:
        print(f" (DELETE USER): {msg}")
        await safe_edit(call, "❌ <b>Yalnyşlyk admine habar ber.</b>", reply_markup=get_panel_menu())

@router.callback_query(F.data == "panel_list")
async def panel_list(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    users = database.get_vpn_users(data.get("selected_server_id"))
    if not users:
        await call.answer("Ulanyjy ýok.")
        return
    btns = [[InlineKeyboardButton(text=f"✏️ {u[1]}", callback_data=f"edit_user_{u[1]}")] for u in users]
    btns.append([InlineKeyboardButton(text="🔙 Yza", callback_data="back_to_panel")])
    await safe_edit(call, "Düzeltmek üçin saýlaň:", reply_markup=InlineKeyboardMarkup(inline_keyboard=btns))

@router.callback_query(F.data == "back_to_panel")
async def back_panel(call: types.CallbackQuery):
    await safe_edit(call, "🌌 Panel:", reply_markup=get_panel_menu())

@router.message(F.text == "🗑 OpenVPN Poz")
async def kbd_uninstall_select(message: types.Message):
    servers = database.get_user_servers(message.chat.id)
    btns = [[InlineKeyboardButton(text=f"🔥 {s['user']}@{s['ip']} (POZ)", callback_data=f"uninstall_vps_{s['id']}")] for s in servers]
    await message.answer("Haýsy serwerden OpenVPN-i doly aýyrmaly?", reply_markup=InlineKeyboardMarkup(inline_keyboard=btns))

@router.callback_query(F.data.startswith("uninstall_vps_"))
async def cb_uninstall(call: types.CallbackQuery):
    server_id = int(call.data.split("_")[2])
    vps = database.get_server_by_id(server_id)
    await safe_edit(call, f"⏳ {vps['ip']} serwerinden OpenVPN pozulýar...")
    
    success, msg = await ssh_manager.uninstall_async(vps)
    if success:
        await safe_edit(call, "✅ Pozuldy. Serwer arassa.")
    else:
        print(f" (UNINSTALL): {msg}")
        await safe_edit(call, "❌ <b>Yalnyşlyk admine habar ber.</b>")

async def check_expired_task():
    while True:
        await asyncio.sleep(3600)
        conn = database.sqlite3.connect(database.DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT id, admin_id, server_id, username, days, created_at FROM vpn_users")
        users = cursor.fetchall()
        conn.close()
        
        now = datetime.now()
        for u in users:
            try:
                server_id = u[2]
                username = u[3]
                days = u[4]
                created = datetime.strptime(u[5], "%Y-%m-%d %H:%M:%S")
                if now > created + timedelta(days=days):
                    vps = database.get_server_by_id(server_id)
                    if vps:
                        await ssh_manager.revoke_user_async(vps, username)
                        database.delete_vpn_user(server_id, username)
            except: pass

async def main():
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    await bot.delete_webhook(drop_pending_updates=True)
    asyncio.create_task(check_expired_task())
    print("Bot Aktif...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
