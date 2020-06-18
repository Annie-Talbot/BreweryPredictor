"""This program is a brewhouse simulation that can be used to provide
recommendations on future actions to take. It uses a brewery's current status
and previous sales information to predict and suggest actions to take next."""

from tkinter import Tk, Label, Frame, StringVar, IntVar, OptionMenu, Spinbox, Button, Entry
from tkinter.filedialog import askopenfilename
from tkinter import messagebox
from pandas import to_datetime
from datetime import datetime
from math import ceil
import csv
import json


SALES_FILEPATH = 'data/sales_data.json'
TANKS_FILEPATH = 'data/tanks_status.json'
BOTTLES_FILEPATH = 'data/bottle_quantities.json'
APP = None


def test() -> bool:
    """This function runs tests to ensure that the program will run smoothly.

    The required files are checked to ensure they exist.
    Some functions are then also tested.

    Returns:
    bool - represents whether the program is good to run (True = good,
                                                          False = bad)
    """
    try:
        # Checks if the JSON files for the program exist
        open(SALES_FILEPATH, 'r')
        open(TANKS_FILEPATH, 'r')
        open(BOTTLES_FILEPATH, 'r')
        open('data/reset/sales_data.json', 'r')
        open('data/reset/bottle_quantities.json', 'r')
        open('data/reset/tanks_status.json', 'r')
    except FileNotFoundError:
        return False

    update_predicted_demand()
    amend_sales_data(True, 'data/testing/test.csv')
    return True


def reset_system_files():
    """Resets all JSON data files by replacing them with the original files."""
    if messagebox.askyesno("Warning", "Are you sure you want to reset all "
                                      "data?"):
        try:
            # Reset sales data
            with open('data/reset/sales_data.json', 'r') as file:
                reset_json = json.load(file)
            with open(SALES_FILEPATH, 'w+') as file:
                json.dump(reset_json, file)
            # Reset bottle quantities
            with open('data/reset/bottle_quantities.json', 'r') as file:
                reset_json = json.load(file)
            with open(BOTTLES_FILEPATH, 'w+') as file:
                json.dump(reset_json, file)
            # Reset tank status data
            with open('data/reset/tanks_status.json', 'r') as file:
                reset_json = json.load(file)
            with open(TANKS_FILEPATH, 'w+') as file:
                json.dump(reset_json, file)
            # Update displays
            update_bottle_quantities_display()
            update_tanks_status_display()

        except FileNotFoundError:
            messagebox.showerror("File Error", "Couldn't find the reset files")
            return False
    return True


def update_predicted_demand() -> dict:
    """Uses JSON file data to create a weekly average amount of each beer sold.

    The function loads in the JSON file containing previous sales data added by
    the user. A dictionary is created with each element being a week of the
    year. Every week's corresponding value contains the mean average of the
    amount of each beer sold in that week of each year.

    Returns:
    new_predicted_demand: dictionary  - contains the average amount of each
                                        beer sold during each week of the year
    """
    try:
        with open(SALES_FILEPATH, 'r') as file:
            sales_json = json.load(file)
    except OSError:
        return {}
    new_predicted_demand = {}
    # Iterates through every week in the year
    for i in range(1, 53):
        week = ''.join(["week", str(i)])
        # Find the sum total of beers sold for each type of beer, every year
        redhelles_total = 0
        pilsner_total = 0
        dunkel_total = 0
        no_years = 0
        for year in sales_json[week]:
            redhelles_total = redhelles_total + int(year["Organic Red Helles"])
            pilsner_total = pilsner_total + int(year["Organic Pilsner"])
            dunkel_total = dunkel_total + int(year["Organic Dunkel"])
            no_years = no_years + 1
        if no_years == 0:
            no_years = 1
        # Creates this week in the dictionary and assigns it the mean averages
        new_predicted_demand[week] = [round(redhelles_total / no_years),
                                      round(pilsner_total / no_years),
                                      round(dunkel_total / no_years)]

    return new_predicted_demand


def amend_sales_data(is_test: bool, filename: str):
    """Reads a csv file and structures it's data to be saved into a JSON file.

    The function iterates through the csv entries and adds each one into the
    Previous Sales JSON. The information added includes the quantity of
    bottles, the week the order was required, the type of beer and the year of
    order.

    Arguments:
    is_test: boolean - if the function is being tested (True = it is)
    filename: string - filepath of the csv to be accessed.
    """
    with open(SALES_FILEPATH, 'r') as file:
        sales_json = json.load(file)

    with open(filename, 'r') as csvfile:
        try:
            csvreader = csv.reader(csvfile)
            for row in csvreader:
                if row[0] == 'Invoice Number':  # If its the header row, skip
                    continue

                # Working out which week of the year this data is from
                date_string = row[2]
                order_date = datetime.strptime(date_string, '%d-%b-%y')
                year_began_date = datetime(order_date.year - 1, 12, 31)
                difference = order_date - year_began_date
                difference_in_weeks = difference.days / 7
                if difference_in_weeks > 52:
                    difference_in_weeks = 52
                else:
                    difference_in_weeks = int(ceil(difference_in_weeks))
                week = ''.join(['week', str(difference_in_weeks)])

                beer_name = row[3]
                quantity = row[5]
                # Found out the index in the JSON of the year the order is from
                year_index = -1
                no_entries = len(sales_json[week])
                if no_entries != 0:
                    for i in range(0, no_entries):
                        if sales_json[week][i]["year"] == str(order_date.year):
                            year_index = i
                            break
                # Adds data to JSON
                if year_index == -1:
                    new_entry = {"year": str(order_date.year),
                                 "Organic Red Helles": 0, "Organic Pilsner": 0,
                                 "Organic Dunkel": 0, beer_name: quantity}
                    sales_json[week].append(new_entry)
                else:
                    current_value = int(
                        sales_json[week][year_index][beer_name])
                    sales_json[week][year_index][beer_name] = str(
                        current_value +
                        int(quantity))
        except UnicodeDecodeError:
            messagebox.showerror("File Error", "The file selected is not a csv"
                                               " file or spreadsheet.")
        except ValueError:
            messagebox.showerror("File Data Error", "Some invalid data was "
                                                    "found in the csv file. " +
                                 str(row) + "Please fix and try again.")
    if not is_test:
        # Saves new data into the file
        with open(SALES_FILEPATH, 'w') as file:
            json.dump(sales_json, file)


def update_tanks_status_display():
    """Reads the Tank Status JSON and updates the display to these values.

    Opens and reads the Tank JSON and iterates through each tank, adding it's
    values into a string. This string is then used as the display.
    """
    with open(TANKS_FILEPATH, 'r') as file:
        tanks_json = json.load(file)
    tanks = tanks_json["tanks"]
    display_string = "CURRENT TANK STATUS: \n"

    for tank in tanks:
        tanks_string = str(''.join(["Tank ", tank["name"], ": ",
                                    tank["status"], "  ",
                                    tank["beer_name"], " ",
                                    tank["current_volume"], "/",
                                    tank["capacity"], " Litres \n"]))
        display_string = display_string + tanks_string

    APP.change_lbl(APP.tanks_lbl, display_string)


def alter_tanks_data(name: str, new_status: str, beer: str, new_volume: int):
    """Uses user inputted data to change the status of a tank in the JSON file.

    The tkinter interface saves the current value of input object into
    variables, these variables are passed in as the arguments of the function.
    The JSON is loaded in and the values are then used to change a tank's
    status.

    Arguments:
    name: string - the name of the tank to be changed
    new_status: string - the status that the tank now has: Idle/Fermenting/
                            Finished Fermenting/Conditioning
    """
    with open(TANKS_FILEPATH, 'r') as file:
        tanks_json = json.load(file)
    tanks = tanks_json["tanks"]

    # Validation of inputs
    is_valid = True
    volume_possible = False
    for tank in tanks:
        if tank["name"] == name:
            if int(new_volume) <= int(tank["capacity"]):
                volume_possible = True
    if not volume_possible:
        reason = "The volume entered is larger than the selected tank's capacity."
        is_valid = False
    elif name == "R" and new_status == "Conditioning":
        reason = "Tank R can only be used for fermenting."
        is_valid = False
    elif ((name == "G" or name == "H") and
          (new_status == "Fermenting" or new_status == "Finished Fermenting")):
        reason = "Tanks G and H can only be used for conditioning."
        is_valid = False

    # Change tank's data or report error with data inputted
    if not is_valid:
        messagebox.showerror("INPUT ERROR",
                             "Some values entered are impossible." + reason)
    else:
        for tank in tanks:
            if tank["name"] == name:
                tank["status"] = new_status
                tank["beer_name"] = beer
                tank["current_volume"] = str(new_volume)
                if name == "R":
                    if new_status == "Fermenting":
                        tank["date"] = str(datetime.today())
                    else:
                        tank["date"] = "N/A"
    # Write these changes to the file
    with open(TANKS_FILEPATH, 'w') as file:
        json.dump(tanks_json, file)
    update_tanks_status_display()


def append_bottles(add: bool, name: str, no_bottles: int):
    """Uses user inputted data to change the data stored in the bottles JSON.

    Uses tkinter variable values to add or remove a chosen amount of bottles
    from the values representing the current amount of bottles that the brewery
    has prepared.t This is done by changing that value in the bottle JSON.

    Argument:
    add: boolean - represent the decision to add(True) or to remove(False) that
                   amount of bottles
    name: string - holds the name of the type of beer to be changed
    no_bottles: int - holds the amount of beer to be added/removed

    Returns an error if a negative value of bottles is given.
    """
    with open(BOTTLES_FILEPATH, 'r') as file:
        bottles_json = json.load(file)
    if add:
        bottles_json[name] = str(int(bottles_json[name]) + no_bottles)
    else:
        new_value = int(bottles_json[name]) - no_bottles
        # Checks if subtraction would result in a negative quantity
        if new_value < 0:
            messagebox.showerror("Negative Quantity Error",
                                 "The amount of bottles you would like to "
                                 "remove would result in a negative "
                                 "quantity. Please enter a new amount.")
            return
        else:
            bottles_json[name] = str(new_value)
    with open(BOTTLES_FILEPATH, 'w') as file:
        json.dump(bottles_json, file)
    update_bottle_quantities_display()
    return


def update_bottle_quantities_display():
    """Reads the bottle quantity JSON data and sets the display to these values
    """
    with open(BOTTLES_FILEPATH, 'r') as file:
        bottles_json = json.load(file)
    display_string = ''.join(
        ["Organic Pilsner : ", bottles_json["Organic Pilsner"],
         "\nOrganic Red Helles : ", bottles_json["Organic Red Helles"],
         "\nOrganic Dunkel : ", bottles_json["Organic Dunkel"]])
    APP.bottle_quantities_lbl["text"] = display_string


def sort_tanks(tanks: dict, status: str) -> list:
    """Iterates through all tanks returning only tanks with a specified status.

    Using the tank dictionary, the function iterates through them all and
    checks their status. If this status matches the one required (passed in),
    then it is added to a new list in this form(name, volume, capacity). This
    list is returned.

    Arguments:
    tanks: dict - contains the list of tanks from the Tanks JSON
    status: string - the status fo the tanks you would like returned

    Returns:
    selected_tanks: list[list[str, int, int]] - the list of tanks with the
                                                specified status
    """
    selected_tanks = []
    for tank in tanks:
        if tank["status"] == status:
            selected_tanks.append([tank["name"], int(tank["current_volume"]),
                                   int(tank["capacity"])])

    return selected_tanks


def calculate_beer_levels(tanks: dict) -> dict:
    """Creates a dictionary with all details of current beer quantity and need.

    Firstly, the bottle quantity JSON is read and its values added to the
    dictionary. Next, the tank status JSON is used to calculate the total of
    each beer being currently brewed. Lastly, the predicted demand is
    calculated for each week of the year and the quantity needed in the next 8
    weeks is added to the dictionary.

    Arguments:
    tanks: dict - the dictionary containing the tank JSON data

    Returns:
    beer_levels: dict - {"Organic Pilsner": [current quantity: int,
                                             amount in brewing process: int,
                                             amount needed within 8 weeks: int]
                         "Organic Red Helles": [same as above]
                         "Organic Dunkel": [same as above]
                        }
    """
    beer_levels = {"Organic Pilsner": [0, 0, 0],
                   "Organic Red Helles": [0, 0, 0],
                   "Organic Dunkel": [0, 0, 0]}

    # Getting current amount of bottled beer (in litres)
    with open(BOTTLES_FILEPATH, 'r') as file:
        bottles_json = json.load(file)
    beer_levels["Organic Pilsner"][0] = int(
        bottles_json["Organic Pilsner"]) / 2
    beer_levels["Organic Red Helles"][0] = (int(bottles_json["Organic Red Helles"])
                                            / 2)
    beer_levels["Organic Dunkel"][0] = int(bottles_json["Organic Dunkel"]) / 2

    # Getting amount of currently brewing beer
    for tank in tanks:
        if tank["status"] != "Idle":
            beer_levels[tank["beer_name"]][1] = (beer_levels[tank["beer_name"]][1]
                                                 + int(tank["current_volume"]))

    # Calculating the average amounts of beer sold in the next 8 weeks
    today = datetime.today()
    year_began_date = datetime(today.year - 1, 12, 31)
    this_week = (today - year_began_date).days / 7
    if this_week > 52:
        this_week = 52
    else:
        this_week = int(ceil(this_week))
    predicted_demand = update_predicted_demand()
    if predicted_demand != {}:
        i = this_week
        counter = this_week
        while counter < this_week + 8:
            beer_levels["Organic Pilsner"][2] = (beer_levels["Organic Pilsner"][2]
                                                 + predicted_demand["week" + str(i)][1])
            beer_levels["Organic Red Helles"][2] = (beer_levels["Organic Red Helles"][2]
                                                    + predicted_demand[("week" + str(i))][0])
            beer_levels["Organic Dunkel"][2] = (beer_levels["Organic Dunkel"][2]
                                                + predicted_demand[("week" + str(i))][2])
            counter = counter + 1
            if counter > 52:
                i = 1
            else:
                i = i + 1
        return beer_levels
    else:
        return {}


def get_next_beer(beer_levels: dict):
    """Calculates which beer should be brewed next.

    The function works out the difference between the amount of already
    prepared and currently brewing beers, and the amount of beers that is
    predicted to be sold in the next 8 weeks.

    Arguments:
    beer_levels: dict - contains the previously calculated values to be used
                        when working out which beers to be used next. A more
                        detailed can be found in the calculate_beer_levels
                        function.
    Returns:
    next_beer: str - the name of the beer type to be brewed next.
    """
    names = ["Organic Pilsner", "Organic Red Helles", "Organic Dunkel"]
    highest_value = -50000
    next_beer = ""
    for beer in names:
        beer_needed = beer_levels[beer][2] - (beer_levels[beer][0] +
                                              beer_levels[beer][1])
        if beer_needed > highest_value:
            next_beer = beer
            highest_value = beer_needed
    if highest_value < 0:
        next_beer = next_beer + " "
    return next_beer


def get_recommendations():
    """Compiles the display text containing the latest brewery recommendations.

    Creates lists containing the tanks that require a new recommendation, split
    by their status. It is then calculated if the unique situation that means
    it would be more efficient to condition beer from any tank other than R in
    tanks G and H. The unique situation: R is not going to have finished
    fermenting before G and H have finished conditioning (R has been brewing
    for less than 2 weeks), G and H ae Idle, another tank's brew needs
    conditioning.
    After, all tanks with fermented beer are suggest to condition the beer in
    the same tank it is in. For any idle tanks, they are ordered into largest
    volume first and the next most required beer is calculated and suggest to
    each tank.
    These recommendations are joined together and displayed on the GUI.
    """
    with open(TANKS_FILEPATH, 'r') as file:
        tanks_json = json.load(file)
    tanks = tanks_json["tanks"]
    display_string = []
    idle_tanks = sort_tanks(tanks, "Idle")
    fin_ferm_tanks = sort_tanks(tanks, "Finished Fermenting")
    if tanks[8]["date"] == "N/A":
        r_brew_time = 1
    else:
        r_brew_time = (datetime.today() - to_datetime(
            tanks[8]["date"])).days / 7
    if (['G', 0, 680] in idle_tanks and ['H', 0, 680] in idle_tanks and
            (r_brew_time < 2 and len(fin_ferm_tanks) > 0)):
        largest_tank_volume = 0
        for tank in fin_ferm_tanks:
            if tank[1] > largest_tank_volume:
                largest_tank_volume = tank[1]
                best_tank = tank
        display_string.append("Tank R2D2 should be fermenting for at least " +
                              "another 2 weeks so you \n should move Tank " +
                              best_tank[0] + "'s contents into Tanks G and " +
                              "H for conditioning. \n")
        fin_ferm_tanks.remove(best_tank)
        idle_tanks.append(best_tank)
    for tank in fin_ferm_tanks:
        if tank[0] == 'R':
            if ['G', 0] in idle_tanks and ['H', 0] in idle_tanks:
                display_string.append("Tank R2D2 can be moved into tanks G" +
                                      "and H for conditioning. \n")
            else:
                display_string.append("Tanks G and H should have almost" +
                                      "finished conditioning, so Tank R2D2's" +
                                      " contents can be moved into them. \n")
        else:
            display_string.append("Tank " + tank[0] + " should be " +
                                  "conditioned in the tank it is currently" +
                                  " in (Tank " + tank[0] + "). \n")

    idle_tanks = sorted(idle_tanks, key=lambda l: l[2], reverse=True)
    beer_levels = calculate_beer_levels(tanks)
    enough = False
    if beer_levels != {}:
        for tank in idle_tanks:
            suggested_beer = get_next_beer(beer_levels)
            if suggested_beer != suggested_beer.strip() and not enough:
                display_string.append("From this point, you have enough beer "
                                      "brewed for the next 8 weeks. \n")
                enough = True
            suggested_beer = suggested_beer.strip()
            display_string.append("Tank " + tank[
                0] + " should be filled with " + suggested_beer + " next. \n")
            complete_tank = next((index for (index, d) in enumerate(tanks) if
                                  d["name"] == tank[0]), None)
            beer_levels[suggested_beer][1] = (beer_levels[suggested_beer][1] +
                                              int(tanks[complete_tank]["capacity"]))
    else:
        display_string.clear()
        display_string.append("No previous sales information entered into "
                              "the system, so no recommendations can be "
                              "made. \n Please append a file --->")
    APP.change_lbl(APP.recommendation_lbl, ''.join(display_string))


class Application(Frame):
    """The GUI for the program.

    Has feature for viewing and changing tank status and amount of bottles
    prepared. You can also add previous sales data to the system and get
    recommendations of what the brewery should do next.
    """
    filename = None
    tanks_lbl_string = None
    tank_name = None
    beer_type = None
    tank_status = None
    current_tank_volume = None
    no_bottles = None

    def select_file(self):
        """Opens a file browsing window and enables user to select a file."""
        self.filename.set(askopenfilename())
        self.filepath_txt["textvariable"] = self.filename

    def change_lbl(self, lbl: Label, string: str):
        """Method for changing the text of a label."""
        lbl["text"] = string

    def create_widgets(self):
        """Creates all features of the GUI and places them on the frame."""
        self.title = Label(self, text="BREWHOUSE SIMULATOR")
        self.title.grid(columnspan=10, pady=10)

        # Tanks status section
        self.tank_lbl_string.set("CURRENT TANKS STATUS:")
        self.tanks_lbl.grid(rowspan=11, columnspan=5)

        # Current Inventory Section
        self.inventory_title = Label(self, text="CURRENT INVENTORY:")
        self.inventory_title.grid(row=1, column=5, columnspan=2)
        self.bottle_quantities_lbl.grid(row=2, column=5, columnspan=2,
                                        rowspan=3)
        self.beer_type_quan = OptionMenu(self, self.beer_name_for_quan,
                                         "Organic Red Helles",
                                         "Organic Pilsner",
                                         "Organic Dunkel")
        self.beer_type_quan.grid(row=6, column=5)
        self.no_bottles_ent = Spinbox(self, from_=0, to=10000,
                                      textvariable=self.no_bottles)
        self.no_bottles_ent.grid(row=6, column=6)
        self.add_bottles_btn = Button(self, text="ADD BOTTLES",
                                      command=(lambda: append_bottles(True,
                                                                      self.beer_name_for_quan.get(),
                                                                      self.no_bottles.get())))
        self.add_bottles_btn.grid(row=7, column=5)
        self.rmv_bottles_btn = Button(self, text="REMOVE BOTTLES",
                                      command=(lambda: append_bottles(False,
                                                                      self.beer_name_for_quan.get(),
                                                                      self.no_bottles.get())))
        self.rmv_bottles_btn.grid(row=7, column=6)

        # Sales data section
        self.sales_title = Label(self, text="ADD SALES DATA TO SYSTEM:")
        self.sales_title.grid(row=10, column=5, columnspan=2, pady=10)
        self.filename.set("Enter filepath")
        self.filepath_txt = Entry(self, width=20, textvariable=self.filename)
        self.filepath_txt.grid(row=11, column=5)
        self.choose_file_btn = Button(self, text="CHOOSE FILE",
                                      command=self.select_file)
        self.choose_file_btn.grid(row=11, column=6)
        self.update_sales_btn = Button(self, text="APPEND FILE",
                                       command=(lambda: amend_sales_data(False,
                                                                         self.filename.get())))
        self.update_sales_btn.grid(row=12, column=5, pady=5)
        self.reset = Button(self, text="Reset System Data",
                            command=reset_system_files).grid(row=12, column=6,
                                                             pady=5)

        # Change tank status section
        self.choose_tank_lbl = Label(self, text="Edit Tank Status:")
        self.choose_tank_lbl.grid(row=12, columnspan=5)
        self.tank_entry_name = OptionMenu(self, self.tank_name, "A", "B",
                                          "C", "D", "E", "F", "G", "H",
                                          "R").grid(row=13)
        self.tank_entry_name = OptionMenu(self, self.beer_type,
                                          "Organic Red Helles",
                                          "Organic Pilsner",
                                          "Organic Dunkel",
                                          "N/A").grid(row=13, column=1)
        self.tank_entry_name = OptionMenu(self, self.tank_status,
                                          "Idle",
                                          "Fermenting",
                                          "Finished Fermenting",
                                          "Conditioning").grid(row=13,
                                                               column=2)
        self.volume_spinbx = Spinbox(self, from_=0,
                                     to=1000,
                                     textvariable=self.current_tank_volume)
        self.volume_spinbx.grid(row=13, column=3)
        self.add_tank = Button(self, text="Change Tank Status",
                               command=lambda: alter_tanks_data(
                                   self.tank_name.get(),
                                   self.tank_status.get(),
                                   self.beer_type.get(),
                                   str(self.current_tank_volume.get())))
        self.add_tank.grid(row=13, column=4)

        # Recommendations section
        self.recommend_btn = Button(self, text="GET RECOMMENDATION",
                                    command=lambda: get_recommendations())
        self.recommend_btn.grid(row=14, rowspan=5, columnspan=2, pady=20)
        self.recommendation_lbl.grid(row=14, rowspan=5, column=1, columnspan=5)
        self.quit = Button(self, text="QUIT",
                           command=self.quit).grid(row=18, column=6)

    def __init__(self, master=None):
        Frame.__init__(self, master)

        self.filename = StringVar()
        self.tank_lbl_string = StringVar()
        self.tank_name = StringVar()
        self.tank_name.set("A")
        self.beer_type = StringVar()
        self.beer_type.set("Organic Red Helles")
        self.tank_status = StringVar()
        self.tank_status.set("Idle")
        self.current_tank_volume = IntVar()
        self.current_tank_volume.set(0)
        self.tanks_lbl = Label(self, text="CURRENT TANKS STATUS")
        self.recommendation_lbl = Label(self, text="\n\n\nNo recommendations "
                                                   "yet.\n\n\n")
        self.bottle_quantities_lbl = Label(self, text="Getting values")
        self.beer_name_for_quan = StringVar()
        self.beer_name_for_quan.set("Organic Red Helles")
        self.no_bottles = IntVar()
        self.no_bottles.set(0)

        self.grid(sticky="NSEW")
        self.create_widgets()


if __name__ == "__main__":
    if test():
        root = Tk()
        root.minsize(800, 450)
        APP = Application(master=root)
        update_tanks_status_display()
        update_bottle_quantities_display()
        APP.mainloop()
        root.destroy()
    else:
        if messagebox.askokcancel("ERROR", "Couldn't access system files. "
                                           "System files will now be reset and"
                                           " the program quit."):
            reset_system_files()
