import flet as ft
import os
import time
import threading
import json

#json file containing the groceries
GROCERIES_FILE = "groceries.json"

#used to load the items from the json to the page
def load_items():
    #if the file doesnt exist(if no items are added then do nothing)
    if os.path.exists(GROCERIES_FILE):
        try:
            with open(GROCERIES_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            #returns an empty list to not break the program
            print(f"error at loading json content: {e}")
            return []
    #returns an empty list to not break the program
    return []

#used to add new items to the json
def save_items(items):
    try:
        with open(GROCERIES_FILE, "w") as f:
            json.dump(items, f)
    except Exception as e:
        print(f"error saving json: {e}")

def main(page: ft.Page):

    #main page config
    page.title = "family cart"
    page.window.icon = "favicon.png" 
    page.theme_mode = ft.ThemeMode.LIGHT
    page.vertical_alignment = "start"
    page.padding = 20
    page.bgcolor = "#F3FCFC"

    #in page title text
    title = ft.Row(
        controls=[ft.Text("Grocery List", size=28, weight=ft.FontWeight.BOLD, color="#36618e")],
        alignment=ft.MainAxisAlignment.CENTER
    )

    #grocery list appearance
    grocery_list = ft.ListView(expand=1, spacing=5, padding=10, auto_scroll=True)

    #used to update the list for everyone when it changes
    def refresh_list():
        grocery_list.controls.clear()
        
        #Load items from the groceries.json file 
        GROCERY_ITEMS = load_items()
        
        for index, item in enumerate(GROCERY_ITEMS):
            item_index = index

            #used for deleting list items
            def delete_item(e,itemIndex=item_index):
                items = load_items()
                if itemIndex < len(items):
                    items.pop(itemIndex)
                    save_items(items)
                    page.pubsub.send_all("update_list")  

            #used for the checkbox of each item to work
            def checkbox_click(e,itemIndex=item_index):
                items = load_items()
                if itemIndex < len(items):
                    items[itemIndex]["checked"] = e.control.value
                    save_items(items)
                    page.pubsub.send_all("update_list")  
                
                #if checkbox is checked
                if e.control.value:
                    def delete_item_thread(i=itemIndex):
                        time.sleep(10)
                        items = load_items()
                        if i < len(items) and items[i].get("checked"):
                            items.pop(i)
                            save_items(items)
                            page.pubsub.send_all("update_list")
                    threading.Thread(target=delete_item_thread, daemon=True).start()

            #creates the checkbox
            checkbox = ft.Checkbox(value=item["checked"], on_change=checkbox_click, scale=1.1)

            #creates the checkbox label
            item_label = ft.Text(
                item["text"], 
                size=20, 
                expand=True
            )

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

            #adds it to the page
            grocery_list.controls.append(list_row)

            #used to remove the delete button after 30 sec of row creation
            def delete_icon_removal_thread(row=list_row, label=item_label, check_box=checkbox):
                time.sleep(30)
                try:
                    if row in grocery_list.controls:
                        row.controls = [check_box, label]
                        page.update()
                except Exception:
                    pass
            threading.Thread(target=delete_icon_removal_thread, daemon=True).start()

        page.update()


    #used to catch all messages by all users 
    def sync_function(message):
        if message == "update_list":
            refresh_list()
    page.pubsub.subscribe(sync_function)

    #used to add an item to the list
    def add_item(e):
        #if the searchbar is empty do nothing
        if not add_item_searchbar.value.strip():
            return

        
        items = load_items()
        items.append({"text": add_item_searchbar.value.strip(), "checked": False})
        save_items(items)

        add_item_searchbar.value = ""
        add_item_searchbar.focus()
        page.pubsub.send_all("update_list")  

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
        ft.Divider(height=20),
        input_row,
        ft.Divider(height=20),
        grocery_list
    )

    #gets the initial list when first opening the page
    refresh_list()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    ft.app(target=main, view=ft.AppView.WEB_BROWSER, port=port, host="0.0.0.0", assets_dir="assets")