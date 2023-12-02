'''Bitcoin Window Module.

This module provides a GUI window for displaying Bitcoin information.
'''

import warnings
from concurrent.futures import ThreadPoolExecutor
import json
import gi
import requests
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, Pango, GdkPixbuf, Gdk

# Unterdrücke Deprecation-Warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)


class BitcoinInfo:
    """Interface for querying Bitcoin information."""

    def __init__(self, currency_code):
        """Initializes the BitcoinInfo class with a currency code option."""
        self.currency_code = currency_code
        self.selected_currency = "EUR"  # Standardwährung
        self.base_currency = "BTC"  # Basiskryptowährung für Wechselkurse
        self.update_url()  # Aktualisiert die URLs basierend auf den aktuellen Werten

    def update_url(self):
        """Updates the URLs based on the base currency and the selected currency."""
        self.url = (
        f"https://api.coinbase.com/v2/prices/{self.base_currency}-{self.currency_code}/buy"
        )
        self.url_block = (
        "https://mempool.space/api/blocks/tip/height"
        )
        self.fee = (
        "https://mempool.space/api/v1/fees/recommended"
        )
        self.hashrate = (
        "https://mempool.space/api/v1/mining/hashrate/1w"
        )
        self.unconf_tx = (
        "https://mempool.space/api/mempool"
        )

    def add_commas(self, number):
        """Adds thousands separators to numbers."""
        return f"{number:11,.0f}".replace(',', '.')

    def get_data(self, url):
        """Retrieves data from the specified URL."""
        with requests.get(url, timeout=10) as response:
            return response.text

    def get_bitcoin_price(self):
        """Retrieves data from APIs in parallel threads and returns formatted information."""
        urls = [self.url, self.url_block, self.fee, self.hashrate, self.unconf_tx]
        with ThreadPoolExecutor(max_workers=6) as executor:
            responses = list(executor.map(self.get_data, urls))

        # Überprüfen Sie den Erfolg der API-Aufrufe
        for response in responses:
            if not response:
                return "Error retrieving data from one of the APIs."

        # Verarbeiten Sie die erhaltenen Daten
        block = json.loads(responses[1])
        fees_data = json.loads(responses[2])
        price_data = json.loads(responses[0])
        hashrate_data = json.loads(responses[3])
        unc_transaction_data = json.loads(responses[4])

        # Extrahieren Sie relevante Informationen aus den Daten
        economy_fee = fees_data['economyFee']
        hour_fee = fees_data['hourFee']
        half_hour_fee = fees_data['halfHourFee']
        fastest_fee = fees_data['fastestFee']

        price_str = price_data['data']['amount']
        price = float(price_str.replace(',', ''))

        hashrate_ehs = float(hashrate_data['currentHashrate']) / 1000000000000000
        utx = unc_transaction_data['count']

        moscow_time = 100000000 / price

        # Erstellen Sie einen formatierten Text mit den extrahierten Informationen
        output = f"BTC ➔ {self.currency_code}\n\n"
        output += f"Bitcoin       :{self.add_commas(price)}\n"
        output += f"Moscow Time   :{self.add_commas(moscow_time)}\n\n"
        output += f"No Fee        :{self.add_commas(economy_fee)}\n"
        output += f"Low Fee       :{self.add_commas(hour_fee)}\n"
        output += f"Medium Fee    :{self.add_commas(half_hour_fee)}\n"
        output += f"High Fee      :{self.add_commas(fastest_fee)}\n\n"
        output += f"Block Height  :{self.add_commas(int(block))}\n"
        output += f"Hashrate (PH) :{self.add_commas(hashrate_ehs)}\n"
        output += f"Unconfirmed   :{self.add_commas(utx)}"


        return output


class CurrencyMenu:
    """This class represents the currency menu."""

    currencies = {
        "EU Euro": "EUR",
        "US Dollar": "USD",
        "Russian Ruble": "RUB",
        "Chinese Yuan": "CNY",
        "Japanese Yen": "JPY",
        "Canadian Dollar": "CAD",
        "Australian Dollar": "AUD",
        "Swiss Franc":"CHF",
        "British Pound": "GBP",
        "Brazilian Real": "BRL",
        "Argentine Peso": "ARS",
        "Norwegian Krone": "NOK",
        "Hungary Forint": "HUF",
        "Mexican Peso":"MXN",
        "Turkish Lira": "TRY",
        "South Korean Won": "KRW",
        "Polish Zloty": "PLN",
    }

    def __init__(self, callback):
        """Initializes the currency menu with a callback."""
        self.currency_menu = Gtk.Menu()
        group = None

        for currency, currency_code in self.currencies.items():
            item = Gtk.RadioMenuItem.new_with_label(group, currency)
            item.connect("activate", callback, currency, currency_code)
            group = item.get_group()
            self.currency_menu.append(item)

        self.currency_menu_item = Gtk.ImageMenuItem.new_with_label("")
        self.currency_menu_item.set_image(Gtk.Image.new_from_icon_name("globe", Gtk.IconSize.MENU))
        self.currency_menu_item.set_submenu(self.currency_menu)


class IntervalMenu:
    """This class represents the interval menu."""

    default_interval = 60

    intervals = {
        "01 min": 60,
        "02 min": 120,
        "05 min": 300,
        "10 min": 600,
        "15 min": 900,
        "30 min": 1800,
        "01 hrs": 3600,
    }

    def __init__(self, callback):
        """Initializes the interval menu with a callback."""
        self.interval_menu = Gtk.Menu()
        group = None

        for interval in self.intervals:
            item = Gtk.RadioMenuItem.new_with_label(group, interval)
            item.connect("activate", callback, self.intervals[interval])
            group = item.get_group()
            self.interval_menu.append(item)

        self.interval_menu_item = Gtk.ImageMenuItem.new_with_label("")
        self.interval_menu_item.set_image(Gtk.Image.new_from_icon_name(
        "chronometer", Gtk.IconSize.MENU
        ))
        self.interval_menu_item.set_submenu(self.interval_menu)


class HelpMenu:
    """This class represents the help menu."""

    def __init__(self, icon_path):
        """Initializes the HelpMenu with a path to the icon."""
        self.icon_path = icon_path
        self.help_menu_item = self.create_help_menu()

    def create_help_menu(self):
        """Creates the help menu."""
        help_menu = Gtk.Menu()

        help_menu_item = Gtk.ImageMenuItem.new_with_label("")
        help_menu_item.set_image(Gtk.Image.new_from_icon_name(
        "help-about", Gtk.IconSize.MENU
        ))
        help_menu_item.set_submenu(help_menu)

        # Verbinden Sie das "Hilfe" Menüelement mit der Methode show_about_dialog
        help_menu_item.connect("button_press_event", self.on_help_menu_click)

        # Entfernen Sie das leere Menü
        help_menu_item.get_submenu().remove(help_menu)

        return help_menu_item

    def on_help_menu_click(self, widget, event):
        """Displays the About dialog box when the Help menu is clicked."""
        if event.type == Gdk.EventType.BUTTON_PRESS and event.button == 1:
            self.show_about_dialog(widget)

    def show_about_dialog(self, widget):
        """Displays the About dialog box."""
        about_dialog = Gtk.AboutDialog()

        # Setzen Sie das Icon für den Über-Dialog
        about_dialog.set_logo(GdkPixbuf.Pixbuf.new_from_file_at_size(self.icon_path, 256, 256))

        about_dialog.set_program_name("Bitcoin Info")
        about_dialog.set_version("0.3.71")
        about_dialog.set_authors(["Zwegen"])
        about_dialog.set_website("https://coinos.io/qr/btc-info%40coinos.io")
        about_dialog.set_website_label("Donation (sats)")
        about_dialog.set_comments("Relevant BTC information at a glance.")

        about_dialog.run()
        about_dialog.destroy()


class MyWindow(Gtk.Window):
    """This class represents the main window of the application."""

    def __init__(self):
        """Initializes the main window of the application."""
        Gtk.Window.__init__(self, title="Bitcoin Info")
        self.currency = "EUR"
        self.set_icon_from_file("/usr/share/btc-info/btc-info.png")
        self.icon_path = "/usr/share/btc-info/btc-info.png"
        self.bitcoin_info = BitcoinInfo(self.currency)  # BitcoinInfo-Instanz erstellen

        # Erstelle die Menüs als Attribute der Klasse
        self.menubar = Gtk.MenuBar()
        self.setup_currency_menu()
        self.setup_interval_menu()
        self.setup_refresh_button()  # Hinzugefügt: Refresh-Button
        self.setup_help_menu()

        self.setup_ui()

        # Zurücksetzen des Zählers für Währungsaktualisierungen
        self.refresh_counter = 0

        self.timeout_id = 0  # Hinzugefügt: Initialisierung von timeout_id
        self.update_interval_seconds = IntervalMenu.default_interval  # Standardintervall
        self.on_auto_refresh()
        self.timeout_id = GLib.timeout_add(
        self.update_interval_seconds * 1000, self.on_auto_refresh
        )
        self.show_all()

    def run_script(self):
        """Executes the script and returns the output."""
        output = self.bitcoin_info.get_bitcoin_price()
        print(f"Output from run_script:\n{output}")
        print("Script execution completed.")
        return output

    def update_textview(self, output):
        """Refreshes the text view with the specified output."""
        self.textbuffer.set_text("")
        end_iter = self.textbuffer.get_end_iter()
        self.textbuffer.insert(end_iter, output)

        adj = self.textview.get_vadjustment()
        adj.set_value(adj.get_upper() - adj.get_page_size())

    def on_auto_refresh(self):
        """Auto-refresh by script execution, updates text view and returns true."""
        output = self.run_script()
        self.update_textview(output)
        return True

    def on_update_interval(self, seconds):
        """Handles the change to the update interval."""
        self.update_interval_seconds = seconds
        self.refresh_counter = 0
        GLib.source_remove(self.timeout_id)
        self.timeout_id = GLib.timeout_add(
        self.update_interval_seconds * 1000, self.on_auto_refresh
        )
        self.on_auto_refresh()

    def on_currency_change(self, widget, label, currency_code):
        """Deals with the change in currency."""
        print(f"Currency changed to {label} ({currency_code})")
        self.currency = currency_code
        self.bitcoin_info.currency_code = currency_code
        self.bitcoin_info.selected_currency = label
        self.bitcoin_info.update_url()

        # Nur den Timeout verwenden, um die Aktualisierung auszulösen
        GLib.source_remove(self.timeout_id)
        self.timeout_id = GLib.timeout_add(self.
        update_interval_seconds * 1000, self.on_auto_refresh
        )
        self.update_textview(self.run_script())

    def on_refresh(self, widget):
        """Handles the click on the refresh button."""
        print("Refresh button clicked")
        output = self.run_script()
        self.update_textview(output)

    def setup_currency_menu(self):
        """Sets up the currency menu."""
        self.currency_menu = CurrencyMenu(self.on_currency_change)

        # Currency Menu (Icon: institution)
        currency_menu_item = self.currency_menu.currency_menu_item
        self.menubar.append(currency_menu_item)

    def setup_interval_menu(self):
        """Sets the interval menu."""
        self.interval_menu = IntervalMenu(self.on_update_interval)

        # Interval Menu (Icon: history)
        interval_menu_item = self.interval_menu.interval_menu_item
        self.menubar.append(interval_menu_item)

    def setup_refresh_button(self):
        """Sets the refresh button."""
        # Refresh Menu (Icon: reload)
        refresh_menuitem = Gtk.MenuItem()
        refresh_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        refresh_box.pack_start(Gtk.Image.new_from_icon_name(
        "reload", Gtk.IconSize.MENU), False, False, 0
        )
        refresh_box.pack_start(Gtk.Label(label=""), False, False, 0)
        refresh_menuitem.add(refresh_box)
        refresh_menuitem.connect("activate", self.on_refresh)
        self.menubar.append(refresh_menuitem)

    def setup_help_menu(self):
        """Opens the help menu."""
        help_menu = HelpMenu(self.icon_path)
        help_menu_item = help_menu.help_menu_item
        self.menubar.append(help_menu_item)

    def setup_ui(self):
        """Sets up the user interface."""
        main_box = Gtk.VBox()
        self.add(main_box)

        main_box.pack_start(self.menubar, False, False, 0)

        text_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, margin=8)
        main_box.pack_start(text_box, True, True, 0)

        self.textview = Gtk.TextView()
        self.textview.set_editable(False)
        self.textbuffer = self.textview.get_buffer()

        font_desc = Pango.FontDescription("Ubuntu Mono, Monospace 12")
        self.textview.override_font(font_desc)

        text_box.add(self.textview)

        self.connect("destroy", Gtk.main_quit)


if __name__ == "__main__":
    win = MyWindow()
    Gtk.main()
