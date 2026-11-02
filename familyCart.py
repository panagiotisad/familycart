import flet as ft
import os
import time
import threading
import json
import random
import supermarket_scrapper,products_matching
from datetime import datetime
from zoneinfo import ZoneInfo


#json file containing the groceries
GROCERIES_FILE = "groceries.json"
file_lock = threading.Lock()
refresh_list_lock = threading.Lock()

#used to load the items for the specific room from the json to the page
def load_room_items(room_name):
    #if the file doesnt exist(if no items are added then do nothing)
    with file_lock:
        if os.path.exists(GROCERIES_FILE):
            try:
                with open(GROCERIES_FILE, "r") as f:
                    data = json.load(f)
                    #if it cant retrieve room_name data it returns an empty array
                    return data.get(room_name,[])
            except Exception as e:
                #returns an empty list to not break the program
                print(f"error at loading json content: {e}")
                return []
    #returns an empty list to not break the program
    return []

#used to add new items to the json
def save_room_items(room_name,items):
    with file_lock:
        data = {}
        if os.path.exists(GROCERIES_FILE):
                try:
                    with open(GROCERIES_FILE, "r") as f:
                        data = json.load(f)
                except Exception as e:
                    print(f"error at reading json content: {e}")
                    pass
        data[room_name] = items
        try:
            with open(GROCERIES_FILE + ".tmp", "w") as f:
                json.dump(data, f)
            os.replace(GROCERIES_FILE + ".tmp", GROCERIES_FILE)
        except Exception as e:
            print(f"error saving json: {e}")

#runs the scrapper each day at 6 am 
def scraper_loop():
    last_run = None
    while True:
        now = datetime.now(ZoneInfo("Europe/Athens"))
        if now.hour == 6 and now.minute == 0 and last_run != now.date():
            last_run = now.date()
            try:
                supermarket_scrapper.run_scrapper()
            except Exception as e:
                print(f"scraper failed: {e}")
        time.sleep(30)


def main(page: ft.Page):

    #main page config
    page.title = "familyCart"
    page.window.icon = "favicon.png" 
    page.theme_mode = ft.ThemeMode.LIGHT
    page.vertical_alignment = "start"
    page.padding = 20
    page.bgcolor = "#F3FCFC"

    #function to pop the last page on the stack
    def pop_page(e):
        page.views.pop()
        page.update()

    #offers page
    def offers_page(item_text,matches):
       
        #added height to have some free space on top 
        offers = [ft.Container(height=30)]

        for score,offer in matches:
            if "sklavenitis" in offer["link"]:
                supermarket_name = "Σκλαβενιτης"
                supermarket_color = "#F5830A"
            elif "ab" in offer["link"]:
                supermarket_name = "AB"
                supermarket_color = "#2D5FC9"
            #fixes a spacing error in sklavenitis offer text
            offer_text = offer["product_offer"]
            if "Δώρο" in offer["product_offer"]:
                offer_text = offer["product_offer"].replace("Δώρο"," Δώρο")
            offers.append(ft.Row(
                [
                ft.Text(
                    offer["product_name"] + "  ",
                    size=16,
                    expand=True,
                    spans=[
                        ft.TextSpan(
                            f"{offer["price"]}€  ",
                            style=ft.TextStyle(color="#4DBA17", weight=ft.FontWeight.BOLD),
                    ),
                    ft.TextSpan(
                        f"{offer_text}  ",
                        style =ft.TextStyle(color="#DA6B21",weight=ft.FontWeight.BOLD),
                    ),
                    ft.TextSpan(
                        f"{supermarket_name}  ",
                        style=ft.TextStyle(color=supermarket_color,weight=ft.FontWeight.BOLD),
                    ),
                ],
            ),
                ft.TextButton(
                    content=ft.Text("see on website", size=16),
                    url=offer["link"],
                    #opens the page in a new tab so the app stays open
                    url_target=ft.UrlTarget.BLANK,
                 ),
                 ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
              )
            )

        
        page.views.append(
            ft.View(
                "/offers",
                offers,
                bgcolor="#F3FCFC",
                scroll=ft.ScrollMode.AUTO,      
                appbar=ft.AppBar(
                    leading=ft.IconButton(icon=ft.Icons.ARROW_BACK, on_click=pop_page,icon_color="#36618e"),
                    title=ft.Text(f"Offers for {item_text}",size=26,color="#36618e",weight=ft.FontWeight.BOLD),
                    center_title=True
                ),
            )
        )
        page.update()
    
    #in page title text and all item offer row 
    matches = products_matching.find_matches("all products")
    title = ft.Row(
    controls=[
        ft.Container(expand=1),
        ft.Container(
            content=ft.Text(
                "Grocery List",
                size=24,
                weight=ft.FontWeight.BOLD,
                color="#36618e",
                text_align=ft.TextAlign.CENTER,
            ),
            expand=2,
            alignment=ft.alignment.center,
        ),
        ft.Container(
            content=ft.TextButton(
                content=ft.Row(
                    controls=[
                        ft.Text("See all offers", size=14, color="#36618e", weight=ft.FontWeight.BOLD),
                        ft.Icon(name=ft.Icons.ARROW_FORWARD, color="#36618e", size=16),
                    ],
                    spacing=2,
                    tight=True,
                ),
                on_click=lambda e, text="all", matches=matches: offers_page(text, matches),
                style=ft.ButtonStyle(padding=0),
            ),
            expand=1,
            alignment=ft.alignment.center_right,
        ),
    ],
    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
    vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    #current room
    user_room = page.client_storage.get("user_room")
    if user_room:
        current_room = user_room
    else:
        room_randomizer = random.randint(1,999999999)
        current_room = "list" + str(room_randomizer)
        page.client_storage.set("user_room", current_room)
    #in page room selection
    room_input = ft.TextField(
        expand=True, 
        height=40,
        text_size=14,
        hint_text="list name..."
    )

    #in page current room text
    room_display = ft.Text(f"Current list: {current_room}", size=14, weight=ft.FontWeight.BOLD, color="#36618e")

    #used to switch rooms
    def switch_room(e):
        #needed to find the current_room variable outside of function scope
        nonlocal current_room
        new_room = room_input.value.strip()
        if not new_room:
            return
        current_room = new_room
        room_display.value = f"Current list: {current_room}"
        page.client_storage.set("user_room", current_room)
        refresh_list()
        page.update()

    #in page switch room button
    room_button = ft.ElevatedButton("Switch list", on_click=switch_room)
    room_row = ft.Row(controls=[room_input, room_button])

    #grocery list appearance
    grocery_list = ft.ListView(expand=1, spacing=5, padding=10, auto_scroll=True)

    #used to update the list for everyone when it changes
    def refresh_list_func():
        grocery_list.controls.clear()
        
        #Load items from the groceries.json file 
        GROCERY_ITEMS = load_room_items(current_room)
        
        for index,item in enumerate(GROCERY_ITEMS):
            item_id = item.get("id")

            #used for deleting list items
            def delete_item(e,itemId =item_id):
                items = load_room_items(current_room)
                for i in items:
                    if i.get("id") == itemId:
                        items.remove(i)
                        break
                save_room_items(current_room,items)
                page.pubsub.send_all(f"update_{current_room}")  

            #used for the checkbox of each item to work
            def checkbox_click(e,itemId =item_id):
                items = load_room_items(current_room)
                for i in items:
                    if i.get("id") == itemId:
                        i["checked"] = e.control.value
                        break
                save_room_items(current_room,items)
                page.pubsub.send_all(f"update_{current_room}")
                
                #if checkbox is checked
                if e.control.value:
                    def delete_item_thread(itemId =itemId):
                        time.sleep(10)
                        items = load_room_items(current_room)
                        for i in items:
                            if i.get("id") == itemId and i.get("checked"):
                                items.remove(i)
                                break
                        save_room_items(current_room,items)
                        page.pubsub.send_all(f"update_{current_room}")
                    threading.Thread(target=delete_item_thread, daemon=True).start()

            #creates the checkbox
            checkbox = ft.Checkbox(value=item["checked"], on_change=checkbox_click, scale=1.1)

            #creates the checkbox label
            item_label = ft.Text(
                item["text"], 
                size=20, 
                expand=True
            )

            if item.get("new_item", False):
                #creates the delete button
                delete_button = ft.IconButton(
                    icon=ft.Icons.DELETE_OUTLINE, 
                    icon_color="red400", 
                    icon_size=28,
                    on_click=delete_item
                )
                #creates the row
                list_row = ft.Row(
                    controls=[checkbox, item_label, delete_button],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER
                )
            else:
                list_row = ft.Row(
                                    controls=[checkbox, item_label],
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                    vertical_alignment=ft.CrossAxisAlignment.CENTER
                                )
            
            #gets the matches for the offers
            matches = products_matching.find_matches(item["text"])
            if matches:
                list_row.controls.append(ft.IconButton(
                    icon=ft.Icons.LOCAL_OFFER,
                    icon_color="#F58F0A",
                    on_click=lambda e, text=item["text"], matches=matches: offers_page(text, matches)))
            #adds it to the page
            grocery_list.controls.append(list_row)
        page.update()


    #using thread lock to only do one refresh at a time
    def refresh_list():
        with refresh_list_lock:
            refresh_list_func()

    #used to catch all messages by all users and update the list of each room when needed
    def sync_function(message):
        if message == f"update_{current_room}":
            refresh_list()
    page.pubsub.subscribe(sync_function)

    #used to add an item to the list
    def add_item(e):
        #if the searchbar is empty do nothing
        if not add_item_searchbar.value.strip():
            return

        item_id = str(random.randint(1, 999999999999))
        items = load_room_items(current_room)
        items.append({"text": add_item_searchbar.value.strip(), "checked": False,"new_item": True,"id":item_id})
        def change_new_item_status_thread():
            time.sleep(30)
            items = load_room_items(current_room)
            for item in items:
                if item.get("id") == item_id:
                    item["new_item"] = False
                    break
            save_room_items(current_room,items)
            page.pubsub.send_all(f"update_{current_room}")
        threading.Thread(target=change_new_item_status_thread, daemon=True).start()
        save_room_items(current_room,items)

        add_item_searchbar.value = ""
        add_item_searchbar.focus()
        page.pubsub.send_all(f"update_{current_room}")

    #creates the searchbar
    add_item_searchbar = ft.TextField(
        hint_text="Add a product...", 
        expand=True,
        on_submit=add_item
    )

    #creates the add button
    add_button = ft.ElevatedButton("Add", icon=ft.Icons.ADD, on_click=add_item)

    #creates the row of the searchbar and add button
    input_row = ft.Row(controls=[add_item_searchbar, add_button])

    #adds the content to the page
    page.add(
        title,
        room_display,
        room_row,
        ft.Divider(height=20),
        input_row,
        ft.Divider(height=20),
        grocery_list
    )

    #gets the initial list when first opening the page
    refresh_list()


if __name__ == "__main__":
    #starts the thread for the scrapper  
    threading.Thread(target=scraper_loop, daemon=True).start()
    port = int(os.environ.get("PORT", 8080))
    ft.app(target=main, view=ft.AppView.WEB_BROWSER, port=port, host="0.0.0.0", assets_dir="assets")