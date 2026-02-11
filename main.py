# StudentID: w24013042 - Robbie Woodruff

# Password is: admin

# Links to help build code.
# Qt For Python -> Documentation: https://doc.qt.io/qtforpython-6/
# Qt.Widgets -> Documentation: https://doc.qt.io/qtforpython-6/

import sys
from enum import Enum
from datetime import date, timedelta, datetime

from PySide6.QtCore import Qt
from PySide6.QtWidgets import *

import random
from faker import Faker  # This program (per assessment) goes off of fake data, as this is just a concept/idea.

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, sessionmaker, declarative_base

# To make this program go off real data, an idea of how to do this is implemented with the SQL database concept.

fake = Faker()
fake.name()
fake.email()
fake.address()



sqlite_file_name = "Licensees.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"
db = sa.create_engine(sqlite_url, echo=True)
Base = declarative_base()
Session = sessionmaker(bind=db)


class LicenseeModel(Base):
    """
    Represents a licensed entity in the system.

    Stores identifying information, licensing details, RHU allocation, and current
    status for each licensee.

    Attributes:
        id (int): Primary key identifier for the licensee.
        name (str): Name of the licensee.
        license_key (int): Unique license key assigned to the specific licensee.
        rhu_allocation (str): RHU allocation associated with the licensee.
        expiration_date (str): Licensee expiration date.
        status (str): Current Licensee status (e.g., Pending, Allocated or Exited).
    """

    __tablename__ = "licensees"

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True)
    name: Mapped[str] = mapped_column()
    license_key: Mapped[int] = mapped_column(unique=True)
    rhu_allocation: Mapped[str] = mapped_column()
    expiration_date: Mapped[str] = mapped_column()
    status: Mapped[str] = mapped_column()

    def __repr__(self) -> str:
        return (f"Licensee(id={self.id}, name={self.name}, license_key={self.license_key}, "
                f"rhu_allocation ={self.rhu_allocation}, expiration_date={self.expiration_date}, status={self.status}.)")


class RHU(Base):
    """
        Represents a Rehabilitation Housing Unit (RHU).

        Stores location and cost information for each RHU used in license
        allocation and ranking.

        Attributes:
            id (int): Primary key identifier for the RHU.
            rhu_id (int): Unique RHU identifier.
            location (str): Location of the RHU -> relevant to requirements (e.g. near school = no sex offenders housed).
            cost_per_day (float): Daily running costs associated with the RHU.
        """

    __tablename__ = "rhu"

    id: Mapped[int] = mapped_column(primary_key=True)
    rhu_id: Mapped[int] = mapped_column(unique=True)
    location: Mapped[str] = mapped_column()
    cost_per_day: Mapped[float] = mapped_column(default=0)

    def __repr__(self) -> str:
        return f"RHU(id={self.id}, rhu_id={self.rhu_id}, location={self.location}, cost_per_day={self.cost_per_day})"


Base.metadata.create_all(db)


class LicenseeStatus(Enum):
    Pending = "Pending"
    Allocated = "Allocated"
    Exited = "Exited"


class Person:
    def __init__(self, name: str, prison_id: str):
        self.name = name
        self.prison_id = prison_id


class Licensee(Person):
    """
    Represents someone on license, including their status (pending, allocated, or exited), requirements
    (mental health support, employment support, etc.) and housing allocation with conflicts included (e.g., sex offender cannot
    live near school).

    Attributes:
        name: (str): Name of the licensee/individual.
        prison_id (str): Unique Prison ID of the licensee/individual.
        status: current status -> Pending, Allocated or Exited.
        notes (str): Health/random notes for the user to create/see from data.
        release_date (date): Planned release date.
        exit_date (datetime): Actual exit date, if not already exited.
        allocated_rhu (RehabilitationHousingUnit): RHU allocation unit assigned.
        sex_offender (bool): Whether licensee is a sex offender -> if yes, cannot be housed in RHUs near schools.
        requires_mental_health (bool): Whether licensee requires mental health support.
        requires_employment_support (bool): Whether licensee requires employment support -> Will be housed in a RHU that is appropriate to these requirements.
    """

    def __init__(self, name: str, prison_id: str):
        super().__init__(name, prison_id)
        self.status = LicenseeStatus.Pending
        self.notes = ""
        self.release_date = date.today() + timedelta(days=random.randint(1, 100))
        self.exit_date = None
        self.allocated_rhu = None
        self.requirements = []
        self.sex_offender = random.choice([True, False])
        self.requires_mental_health = random.choice([True, False])
        self.requires_employment_support = random.choice([True, False])

    def days_remaining(self):
        """
        Calculates the number of days remaining until release/exit.

        Returns:
             int or None: Days remaining; None if the licensee has already exited.
        """

        if self.status == LicenseeStatus.Exited:
            return None
        target = self.exit_date if self.exit_date else self.release_date
        return (target - date.today()).days

    def display_text(self) -> str:
        """
        Formats variables to ensure the text the user sees is not technical and developer-esque.

        Returns:
            str: Formatted variables into a sentence to output understandable text.
        """

        remaining = self.days_remaining()
        day_remain = f"| Days Remaining: {remaining}" if remaining is not None else ""
        rhu_info = f"| RHU: {self.allocated_rhu.name}" if self.allocated_rhu else ""
        return f"Name: {self.name}, Prison ID: {self.prison_id}, Status: {self.status.value} {day_remain} {rhu_info}"

    def __str__(self):
        return self.display_text()


class RehabilitationHousingUnit:
    """
    Represents a housing unit (RHU) for licensees, including the housing units components such as
    capacity, running costs, and supported services (e.g. mental health support, employment support, etc.)

    Attributes:
        name: (str): Name of the RHU.
        capacity (int): Maximum number of licensees RHU can hold.
        cost (float): Cost per licensee/day.
        licensees (list): List of currently allocated Licensees.
        supports_mental_health (bool): Whether RHU provides mental health support.
        supports_employment (bool): Whether RHU provides employment support.
        near_school (bool): Whether RHU is located near school.
    """

    def __init__(self, name: str, capacity: int, cost: float):
        self.name = name
        self.capacity = capacity
        self.cost = cost
        self.licensees = []
        self.attributes = []
        self.supports_mental_health = random.choice([True, False])
        self.supports_employment = random.choice([True, False])
        self.near_school = random.choice([True, False])

    def has_space(self):
        """
        Checks if the RHU has available space to house a new licensee.

        Returns:
            bool: True if the RHU has available space to house a new licensee, False otherwise.
        """

        return len(self.licensees) < self.capacity

    def near_school_safeguard(self, licensee):
        """
        Checks if the RHU is near a school, if so, cannot house sex offender licensees.

        Returns:
             bool: False if the RHU is near a school and the licensee is a sex offender, True otherwise.
        """

        if self.near_school and licensee.sex_offender:
            return False
        return True

    def daily_cost(self):
        """
        Calculates the total daily running costs for all licensees currently housed in this RHU.

        Returns:
            float: Total daily cost.
        """

        return len(self.licensees) * self.cost

    def __str__(self):
        return f"RHU(Name: {self.name}, Capacity: {self.capacity}, Cost: £{self.cost}/day)"

class Ranking_Sys:
    """
    Base class for scoring system used to rank RHUs against each other based on
    specific licensee needs.
    """

    def score_against(self, other):
        return 0

class MentalHealthSup(Ranking_Sys):
    """
    Scores an RHU based on whether it
    supports mental health services required by the specific licensee.
    """

    def score_against(self, other):
        """
        Returns a score for matching mental health requirement.

        Args:
            other (str): RHU attribute to compare.

        Returns:
            int: Score (2 if matches mental health services, 0 otherwise).
        """

        return 2 if other == "mental_health" else 0

class EmploymentSup(Ranking_Sys):
    """
    Scores an RHU based on whether it
    supports employment services required by the specific licensee.
    """

    def score_against(self, other):
        """
        Returns a score for matching employment support requirement.

        Args:
            other (str): RHU attribute to compare.

        Returns:
            int: Score (1 if matches employment support services, 0 otherwise).
        """

        return 1 if other == "employment" else 0

class Allocation:
    """
    Handles ranking of Rehabilitation Housing Units (RHUs) based on:
    - licensee needs
    - safeguarding rules
    - capacity
    """

    @staticmethod  # Added after using PyCharm's code problems checker.
    def rank(licensee: Licensee, rhus):
        """
        Ranks all RHUs for a specific licensee.

        Args:
            licensee (Licensee): The licensee to match.
            rhus (list[RehabilitationHousingUnit]): List of RHUs to consider.

        Returns:
            list of tuple: Each tuple contains (RHU, score, conflicts), sorted by a descending suitability score.
        """

        results = []

        for rhu in rhus:
            score = 0
            conflicts = []
            if licensee.requires_mental_health and rhu.supports_mental_health:
                score += 5
            if licensee.requires_employment_support and rhu.supports_employment:
                score += 3
            if not rhu.near_school_safeguard(licensee):
                conflicts.append("Sex Offender, RHU is Near School = Safeguarding Breach.")
                score -= 100
            if not rhu.has_space():
                conflicts.append("No Capacity")
                score -= 100

            results.append((rhu, score, conflicts))
        results.sort(key=lambda x: x[1], reverse=True)
        return results


# This is the first page created when running the program. This will be the start point of the program, other pages will be directed by this page.
class Login_Page(QWidget):
    """
    Login page for the In-House On-License Housing Allocation System.

    Attributes:
        Password_Correct (str): Constant password for login to compare to user inputted password.
    """

    Password_Correct = "admin"

    def __init__(self):
        super().__init__()
        self.main = None  # Added after using PyCharm's code problems checker.
        self.login_counter = 0
        self.setWindowTitle("On-License Housing Allocation - Login Page")
        layout = QVBoxLayout()
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)
        login_button = QPushButton("Login")
        login_button.clicked.connect(self.check_password)
        layout.addWidget(QLabel("Enter Password:"))
        layout.addWidget(self.password)
        layout.addWidget(login_button)
        self.setLayout(layout)

    def check_password(self) -> None:
        """
        Validates the entered password from the user and compares it to the constant variable (Password Correct) to ensure
        that the password the user entered is correct. As per the specification, a username is not needed/required to log in.

        Returns:
            Password Correct (if correct, welcome user with popup)
            Password Incorrect (if incorrect, attempts + 1 until attempts = 3 then quit)
        """

        if self.password.text() == self.Password_Correct:
            QMessageBox.information(self, "Access Accepted", f"Correct Password. Welcome {self.Password_Correct.capitalize()}!")
            print(f"Correct Password. Welcome {self.Password_Correct.capitalize()}.")  # Print statements for debugging purposes. Makes sure code correctly flows throughout program as designed.
            self.main = Main_Page()
            self.main.show()
            self.close()
        else:
            self.login_counter += 1
            if self.login_counter >= 3:
                QMessageBox.critical(self, "Access Denied", f"Attempts = {self.login_counter}. Try Login Another Time!")
                print(f"Incorrect Password: '{self.password.text()}', For Testing Reasons: Password is '{self.Password_Correct}'. Too Many Login Attempts, Quitting. ")
                QApplication.quit()
            else:
                QMessageBox.warning(self, "Access Denied", f"Incorrect Password, Attempts = {self.login_counter}/3.")
                print(f"Incorrect Password: '{self.password.text()}', For Testing Reasons: Password is '{self.Password_Correct}'.")


class RHURankDialog(QDialog):
    """
    Dialog window to display RHU ranking for a specific licensee, including suitability scores
    and conflicts.

    Args:
        licensee (Licensee): Licensee to match.
        rhus (list[RehabilitationHousingUnit]): List of RHUs to rank.
    """

    def __init__(self, licensee, rhus):
        super().__init__()
        self.setWindowTitle("RHU Matching Results")
        layout = QVBoxLayout(self)

        for rhu, score, conflicts in Allocation().rank(licensee, rhus):
            text = f"{rhu.name} | Score: {score} | £{rhu.cost}/day. | {len(rhu.licensees)}/{rhu.capacity}"
            if conflicts:
                text += f"\nWARNING | " + ";  ".join(conflicts)
            label = QLabel(text)
            if conflicts:
                label.setStyleSheet("color:red;")
            layout.addWidget(label)


class CostReportingDialog(QDialog):
    """
    Dialog window that displays the total daily running costs of all RHUs and individual RHU costs.

    Args:
        rhus (list[RehabilitationHousingUnit]): List of RHUs for reporting costs.
    """

    def __init__(self, rhus):
        super().__init__()
        self.setWindowTitle("RHU Cost Reporting Results")
        layout = QVBoxLayout(self)
        total_cost = 0
        for rhu in rhus:
            cost = rhu.daily_cost()
            total_cost += cost
            layout.addWidget(QLabel(f"{rhu.name}: {len(rhu.licensees)} licensees | £{cost}/day"))
        layout.addWidget(QLabel(f"\nTotal Daily Cost: £{total_cost}."))


def create_fake_licensees():
    """
    Creates fake data for the licensees tables with a name, prison id, whether they require mental health support
    or employment support, etc.

    Returns:
         licensee with fake name, 1000 to 9999 prison id,
         no requirements or mental health support or employment support.
    """

    name = fake.name()
    prison_id = f"W:{random.randint(1000, 9999)}"
    licensee = Licensee(name, prison_id)
    licensee.status = random.choice(list(LicenseeStatus))

    if random.choice([True, False]):
        licensee.requirements.append(MentalHealthSup())
    if random.choice([True, False]):  # Random chance of being true/false, helps to test with different and relevant data.
        licensee.requirements.append(EmploymentSup())
    return licensee


class Main_Page(QWidget):
    """
    Main application window for managing licensees and RHUs.

    Attributes:
        all_licensees (list): List of all Licensees.
        rhus (list): List of RehabilitationHousingUnits.
        pending (QListWidget): GUI List for pending Licensees.
        allocated (QListWidget): GUI List for allocated Licensees.
        exited (QListWidget): GUI List for exited Licensees.
        last_removed (Licensee or None): Last removed exited licensee for the undo functionality to work correctly.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("On-License Housing Allocation - Main Page")
        self.all_licensees = []
        self.rhus = self.create_demo_rhus()
        self.pending = QListWidget()
        self.allocated = QListWidget()
        self.exited = QListWidget()
        layout = QHBoxLayout()
        layout.addLayout(self.column("Pending", self.pending))
        layout.addLayout(self.column("Allocated", self.allocated))
        layout.addLayout(self.column("Exited", self.exited))
        self.setLayout(layout)
        side = QVBoxLayout()
        create_pending_button = QPushButton("Create Pending Licensee")
        create_pending_button.clicked.connect(self.action_pending_licensee)
        side.addWidget(create_pending_button)
        report_dialog_button = QPushButton("View Cost Report")
        report_dialog_button.clicked.connect(self.show_report)
        side.addWidget(report_dialog_button)
        release_button = QPushButton("Release Results")
        release_button.clicked.connect(self.show_imminent_releases)
        side.addWidget(release_button)
        side.addStretch()
        layout.addLayout(side)
        self.pending.itemDoubleClicked.connect(self.pending_allocate)
        self.allocated.itemDoubleClicked.connect(self.allocated_action_dialog)
        self.exited.itemDoubleClicked.connect(self.remove_exited_system)
        self.last_removed = None
        self.load_demo_data(100)

    @staticmethod  # Added after using PyCharm's code problems checker.
    def column(title, widget):
        box = QVBoxLayout()
        box.addWidget(QLabel(title))
        box.addWidget(widget)
        return box

    @staticmethod  # Added after using PyCharm's code problems checker.
    def create_demo_rhus():
        """
        This creates the RHU data (with 6 RHUs created, specific capacities and costs for testing purposes).
        If using real data (SQL) this would not be needed.
        """

        rhus = []
        for i in range(6):
            rhu = RehabilitationHousingUnit(
                name=f"RHU{i + 1}",
                capacity=random.randint(5, 20),
                cost=random.randint(40, 120))
            rhus.append(rhu)
        return rhus

    def load_demo_data(self, count=4000):
        """
        Generates and loads a dataset of fake licensee data into their appropriate lists (Enums - Pending, Allocated, Exited).

        Args:
            count: 4000 -> dataset creation, this program only uses 100 currently for testing.

        Returns:
         Licensees with Pending, Allocated and Exited status' which allow them to be entered into their specific tables.
        """

        for _ in range(count):
            licensee = create_fake_licensees()
            self.all_licensees.append(licensee)
            if licensee.status == LicenseeStatus.Allocated:
                selected_rhu = random.choice(self.rhus)
                licensee.allocated_rhu = selected_rhu
                selected_rhu.licensees.append(licensee)
            item = QListWidgetItem(licensee.display_text())
            item.setData(Qt.UserRole, licensee)
            if licensee.status == LicenseeStatus.Pending:
                self.pending.addItem(item)
            elif licensee.status == LicenseeStatus.Allocated:
                self.allocated.addItem(item)
            else:
                self.exited.addItem(item)

    def allocate_licensee_to_rhu(self, licensee, rhu):
        """
        Allows user to double-click on a user in the pending category table and move them into
        the allocated category table, with other functions allowing the user to select a specific rhu.
        """

        if not rhu.has_space():
            QMessageBox.warning(self, "Allocation Denied", f"{rhu.name} has no space.")
            return
        if not rhu.near_school_safeguard(licensee):
            QMessageBox.warning(self, "Allocation Denied", f"{rhu.name} cannot accept licensee as per safeguarding rules.")
            return
        else:
            licensee.status = LicenseeStatus.Allocated
            licensee.allocated_rhu = rhu
            rhu.licensees.append(licensee)
            item = QListWidgetItem(licensee.display_text())
            item.setData(Qt.UserRole, licensee)
            self.allocated.addItem(item)

    def pending_allocate(self, item: QListWidgetItem):
        """
        This function occurs when a pending licensee is double-clicked by a user (admin).
        This displays RHU ranking and allows the user (admin) to make an allocation.
        Doesn't allow RHU with no capacity to be allocated more licensees, and if an RHU is near a school,
        it cannot be allocated a sex offender licensee.
        """

        licensee = item.data(Qt.UserRole)
        RHURankDialog(licensee, self.rhus).exec()
        available = [rhu.name for rhu in self.rhus if rhu.has_space() and rhu.near_school_safeguard(licensee)]
        if not available:
            return
        name, good = QInputDialog.getItem(self, "Allocate", "Select RHU: ", available, 0, False)
        if not good:
            return
        rhu = next(r for r in self.rhus if r.name == name)
        licensee.status = LicenseeStatus.Allocated
        licensee.allocated_rhu = rhu
        rhu.licensees.append(licensee)
        self.pending.takeItem(self.pending.row(item))
        new_item = QListWidgetItem(licensee.display_text())
        new_item.setData(Qt.UserRole, licensee)
        self.allocated.addItem(new_item)
        print(f"Transferred {licensee.name} to {rhu.name}.")

    def transfer_licensee_rhu(self, item: QListWidgetItem, licensee):
        """
        Transfers a licensee from their current RHU to a new user-selected RHU. User can see suitability
        score and transfer accordingly.

        Ensures that valid RHU specifically for each licensee (sex offender or no capacity, etc.) carries over from
        pending allocate function and still doesn't allow, e.g. sex offender to be transferred to another
        RHU near a school after being allocated.
        """

        available_rhus = [rhu for rhu in self.rhus if rhu.has_space() and rhu.near_school_safeguard(licensee) and rhu != licensee.allocated_rhu]
        if not available_rhus:
            QMessageBox.warning(self, "Error", f"No Valid RHUs Available to Transfer {licensee.name}.")
            return
        else:
            rhu_names = [rhu.name for rhu in available_rhus]
            new_rhu_name, ok = QInputDialog.getItem(self, "Transfer Licensee", "Select New RHU:", rhu_names, 0, False)
            if not ok:
                return
            else:
                new_rhu = next(rhu for rhu in available_rhus if rhu.name == new_rhu_name)
                old_rhu = licensee.allocated_rhu
                if old_rhu and licensee in old_rhu.licensees:
                    old_rhu.licensees.remove(licensee)
                licensee.allocated_rhu = new_rhu
                new_rhu.licensees.append(licensee)
                item.setText(licensee.display_text())

    def transfer_licensee_exited(self, item: QListWidgetItem):
        """
        Allows the user to double-click on allocated Licensees and transfer their status from allocated to exited.
        """

        licensee = item.data(Qt.UserRole)
        if not licensee:
            QMessageBox.warning(self, "Error", f"Licensee Data Missing.")
            return
        else:
            if licensee.status != LicenseeStatus.Allocated:
                QMessageBox.warning(self, "Error", f"Licensee Not Allocated.")
            q1 = QMessageBox.question(self, "Confirm Exit", f"Are you sure you want to transfer {licensee.name} to exited?", QMessageBox.Yes | QMessageBox.No)
            if q1 == QMessageBox.Yes:
                licensee.status = LicenseeStatus.Exited
                licensee.exit_date = datetime.now()
                if licensee.allocated_rhu and licensee in licensee.allocated_rhu.licensees:
                    licensee.allocated_rhu.licensees.remove(licensee)
                licensee.allocated_rhu = None
                row = self.allocated.row(item)
                self.allocated.takeItem(row)
                exited_item = QListWidgetItem(licensee.display_text())
                exited_item.setData(Qt.UserRole, licensee)
                self.exited.addItem(exited_item)

    def allocated_action_dialog(self, item: QListWidgetItem):
        licensee = item.data(Qt.UserRole)
        if not licensee or licensee.status != LicenseeStatus.Allocated:
            return
        else:
            msg = QMessageBox(self)
            msg.setWindowTitle("Allocated Licensee")
            msg.setText(f"Choose what to do with: {licensee.name}.")
            transfer_button = msg.addButton("Transfer RHU", QMessageBox.AcceptRole)
            exit_button = msg.addButton("Exit Licensee", QMessageBox.DestructiveRole)
            msg.addButton(QMessageBox.Cancel)
            msg.exec()
            user_click = msg.clickedButton()

            if user_click == transfer_button:
                self.transfer_licensee_rhu(item, licensee)
                print(f"Transferred {licensee.name} to {licensee.allocated_rhu.name}.")
            elif user_click == exit_button:
                self.transfer_licensee_exited(item)
                print(f"Exited {licensee.name}.")  # For debug reasons, to make sure the code runs to this point, and it is displayed in the console to show it works correctly.

    def remove_exited_system(self, item: QListWidgetItem):
        """
        A function that removes exited licensees to clear data from overcrowding table
        -> promoting usability, readability and clarity.
        """

        licensee = item.data(Qt.UserRole)
        if not licensee or licensee.status != LicenseeStatus.Exited:
            return
        else:
            confirm = QMessageBox.question(self, "Remove Licensee", f"Permanently remove {licensee.name}?", QMessageBox.Yes | QMessageBox.No)
            if confirm != QMessageBox.Yes:
                return
            else:
                row = self.exited.row(item)
                self.exited.takeItem(row)
                if licensee in self.all_licensees:
                    self.all_licensees.remove(licensee)
                self.last_removed = licensee
                print(f"Permanently Removed Exited Licensee: {licensee.name}.")  # Debugging purposes.
                msg = QMessageBox(self)
                msg.setWindowTitle("Undo Removed Exited Licensee")
                msg.setText(f"Would you like to Undo Removal of {licensee.name}?")
                no_button = msg.addButton("No", QMessageBox.ActionRole)
                yes_button = msg.addButton("Yes", QMessageBox.AcceptRole)
                msg.exec()
                user_click = msg.clickedButton()
                if user_click == yes_button:
                    self.undo_remove_licensee()
                    QMessageBox.information(self, "Completed Undo Removal", f"Completed Undo Removal of {licensee.name}.")
                    print(f"Completed Undo Removal of Exited Licensee: {licensee.name}.")  # Debugging purposes.

    def undo_remove_licensee(self):
        """
        Allows the user to undo their removal of an exited Licensee.
        self.last_removed is created at the beginning and saves the previous deleted licensee for undo functionality to work correctly.
        """

        if not self.last_removed:
            return
        else:
            licensee = self.last_removed
            self.last_removed = None
            self.all_licensees.append(licensee)
            item = QListWidgetItem(licensee.display_text())
            item.setData(Qt.UserRole, licensee)
            self.exited.addItem(item)

    def action_pending_licensee(self):
        """
        Logic behind create pending button, ensures that a user is prompted to enter a licensee name
        and assigns an id to them which is then added to the pending licensee table when the
        button is pressed and there's a valid input.
        """

        name, good = QInputDialog.getText(self, "Create Pending Licensee", "Enter Licensee Name")

        if not good or not name.strip():
            QMessageBox.warning(self, "Invalid, Enter Valid Name", "Licensee Name cannot be empty.")
            return
        prison_id = f"W: {random.randint(1000, 9999)}"
        self.create_pending_licensee(name.strip(), prison_id)

    def create_pending_licensee(self, name: str, prison_id: str):
        """
        This is the button to creates a pending licensee, once clicked, action_pending_licensee ensures user
        inputs valid data. This function then ensures that the input is added to the pending licensee table and
        displayed to the user.
        """

        licensee = Licensee(name, prison_id)
        licensee.status = LicenseeStatus.Pending
        self.all_licensees.append(licensee)
        item = QListWidgetItem(licensee.display_text())
        item.setData(Qt.UserRole, licensee)
        self.pending.addItem(item)
        print(f"Created Pending Licensee: {licensee.name}.")

    def show_matches(self, item):
        """
        Displays the RHU ranking dialog for the user double-clicked licensee.

        Extracts the licensee object from the given item and opens an RHURankDialog to display
        matching Rehabilitation Housing Units. Before showing this, checks to make sure if licensee data is present, if missing,
        an error message is show and dialog is not opened.

        Args:
            item(QListWidgetItem): The UI item containing the licensee data stored under Qt.UserRole

        Returns:
            None -> Only shows dialog, not returning any value.
        """

        licensee = item.data(Qt.UserRole)
        if not licensee:  # Code Redundancy checking (or refactoring), tying loose ends -> Making sure that the program reads the data and functions correctly and good for debug. If not used, confusion may occur as program may not work with no explanation.
            QMessageBox.warning(self, "Error", f"Licensee Data Missing")
            return
        else:
            dialog = RHURankDialog(licensee, self.rhus)
            dialog.exec()

    def show_report(self):
        """
        A function that allows a button to appear on the main page to
        show the total cost of running all RHUs.
        """

        CostReportingDialog(self.rhus).exec()

    def show_imminent_releases(self):
        """
        A button that shows licensees close to their release date. Only shows licensees under or equal to 14 days.
        Shows minimum of 14 days remaining as the data currently created to demo this project only has 1 to 100 days remaining.
        Higher/Realistic Data with thousands of entries, this will have to be changed to a lower value to reduce clogging release report screen.
        """

        text = ""
        for rhu in self.rhus:
            text += f"\n{rhu.name}:\n"
            for licensee in rhu.licensees:
                days = licensee.days_remaining()
                if days is not None and days <= 14:
                    text += f"{licensee.name} - {days} days remaining\n"
        QMessageBox.information(self, "Upcoming Release Report", text or "No Upcoming Releases")


if __name__ == '__main__':  # Ensures the program only runs the login page code when the script is run from the name of the python file.
    app = QApplication(sys.argv)
    login = Login_Page()
    login.show()
    sys.exit(app.exec())
