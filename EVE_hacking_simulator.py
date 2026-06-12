from pathlib import Path
from tkinter import PhotoImage
import math
import random
import tkinter
import warnings

# Sets the board size. Try 50 by 50 I dare you. No I did not make a scroll bar.
# 2 by 1 or 1 by 2 is also possible. Not very challenging though.
# The UI prefers widths of 5 and above. Sizes between 6-10 seem common in EVE.
BOARD_HEIGHT = 9
BOARD_WIDTH = 10

# Player starting stats
# - T1 Alpha:               25 strength, 70 coherence
# - T2 Omega:               40 strength, 110 coherence
# - Zeugma + Blackglass:    60 strength, 90 coherence
STRENGTH = 40
COHERENCE = 110

# Fractions should be interpreted as 1/FRACTION, so a value of 4 affects a quarter of the nodes
FRACTION_REMOVED = 4
FRACTION_DEFENSE = 25
FRACTION_UTILITY = 25
FRACTION_CACHE = 25

# Difficulty of the nodes. Options include 'very easy', 'easy', 'medium', 'hard' and 'hardest'
# TODO: Add this, it is nonfunctional for now
DIFFICULTY = "hard"

# No need to change these unless you want to break the layout
HEX = "#030303"
BUTTON_SIZE = 50
X_SPACING = 58
Y_SPACING = 67
PADDING = 50
BOTTOM_SPACE = 100

root = tkinter.Tk()
root.title("EVE Hacking Simulator")
canvas = tkinter.Canvas(root, bg=HEX, highlightthickness=0)
canvas.place(x=0, y=0, relwidth=1, relheight=1)

# Make sure to have an 'images' folder (containing the images) in the same location as this python file!
BASE_DIR = Path(__file__).resolve().parent
IMAGES = {
    "Antivirus": PhotoImage(file=BASE_DIR / "images/Node_antivirus.png"),
    "Core": PhotoImage(file=BASE_DIR / "images/Node_core_hard.png"),
    "Data Cache": PhotoImage(file=BASE_DIR / "images/Node_data_cache.png"),
    "Empty": PhotoImage(file=BASE_DIR / "images/Node_empty.png"),
    "Encrypted": PhotoImage(file=BASE_DIR / "images/Node_encrypted.png"),
    "Firewall": PhotoImage(file=BASE_DIR / "images/Node_firewall.png"),
    "Repair": PhotoImage(file=BASE_DIR / "images/Node_self_repair.png"),
    "Restorer": PhotoImage(file=BASE_DIR / "images/Node_restorer.png"),
    "Rot": PhotoImage(file=BASE_DIR / "images/Node_kernel_rot.png"),
    "Shield": PhotoImage(file=BASE_DIR / "images/Node_polymorphic_shield.png"),
    "Suppressor": PhotoImage(file=BASE_DIR / "images/Node_suppressor.png"),
    "Unexplored": PhotoImage(file=BASE_DIR / "images/Node_unexplored.png"),
    "Vector": PhotoImage(file=BASE_DIR / "images/Node_secondary_vector.png"),
    "Stats": PhotoImage(file=BASE_DIR / "images/Stats.png"),
    "Tool Empty": PhotoImage(file=BASE_DIR / "images/Tool_empty.png"),
    "Tool Shield": PhotoImage(file=BASE_DIR / "images/Tool_polymorphic_shield.png"),
    "Tool Vector": PhotoImage(file=BASE_DIR / "images/Tool_secondary_vector.png"),
    "Tool Repair": PhotoImage(file=BASE_DIR / "images/Tool_self_repair.png"),
    "Tool Rot": PhotoImage(file=BASE_DIR / "images/Tool_kernel_rot.png"),
}


class Node(object):
    def __init__(self, row: int, column: int):
        self.row = row
        self.column = column
        self.empty = False
        self.blocked = False
        self.is_core = False
        self.removed = False
        self.visited = False
        self.distance = None
        self.is_start = False
        self.encounter = None
        self.shown_path = False
        self.can_be_visited = False


class Encounter:
    TYPE = None
    IMAGE_KEY = None
    POWER = None
    TITLE = "Placeholder: text"
    BODY = "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua."

    def __init__(self, player, node=None):
        self.node = node
        self.type = self.TYPE
        self.player = player
        self.image = IMAGES[self.IMAGE_KEY] if self.IMAGE_KEY else None
        self.power = self.POWER
        self.body = self.BODY

    def ability_power(self):
        return self.power

    def turn_into_empty_node(self, events):
        """
        Turns the node into an 'empty node'.
        (It removes the encounter.)
        """
        self.node.empty = True
        self.node.encounter = None
        events.append(("node_update", self.node))


class DataCache(Encounter):
    TYPE = "Data Cache"
    IMAGE_KEY = "Data Cache"
    TITLE = "Data Cache"
    BODY = "Data Caches are archives which can contain Defense or Utility subsystems. Reveal the contents of the Data Cache by left clicking it."

    def __init__(self, player, node=None):
        super().__init__(player, node)
        self.title = self.TITLE
        self.body = self.BODY

    def interact(self, events):
        """
        Datacache turns into a random utility or defense.
        Returns the random utility or defense.
        """
        if random.random() < 0.5:
            random_utility = random.choice(UTILITIES)
            return random_utility(self.player, self.node)
        else:
            random_defense = random.choice(DEFENSES)
            return random_defense(self.player, self.node)


class Utility(Encounter):
    TITLE = "Utility Subsystem"
    BODY = "Utilities are subsystems you can use to boost your hacking efforts. You can collect the Utility by left clicking it if you have a free slot to hold it."
    TOOL_IMAGE_KEY = None
    TOOL_TITLE = "More placeholder text"
    TOOL_BODY = "Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat."
    CHARGES = None

    def __init__(self, player, node=None, slot=None):
        super().__init__(player, node)
        self.title = self.TITLE
        self.body = self.BODY
        self.tool_image_key = self.TOOL_IMAGE_KEY
        self.tool_title = self.TOOL_TITLE
        self.tool_body = self.TOOL_BODY
        self.charges = self.CHARGES
        self.activated = False
        self.slot = slot
        self.player = player
        self.targeting = False

    def interact(self, events):
        """
        This version returns True if utility can be added,
        False if interaction is not possible
        """
        if self.player.add_utility(self):
            self.turn_into_empty_node(events)
            return True
        else:
            return False

    def turn_into_empty_slot(self):
        self.player.utilities[self.slot] = None


class Defense(Encounter):
    instances = []

    def __init__(self, player, node=None):
        super().__init__(player, node)
        self.coherence = self.COHERENCE
        self.strength = self.STRENGTH
        self.title = self.TITLE
        self.body = self.BODY

    def interact(self, events):
        """
        Handles a fight between the virus (player) and the defense subsystem.
        """

        print(
            f" {self.type} has {self.coherence} coherence and {self.strength} strength."
        )
        print(
            f" Virus has {self.player.coherence} coherence and {self.player.suppressed_strength} strength."
        )
        node_coherence_loss = min(self.player.suppressed_strength, self.coherence)
        self.coherence -= node_coherence_loss
        print(f" Virus deals {node_coherence_loss} damage.")
        events.append(("node_coherence_loss", self.node, node_coherence_loss))

        if self.coherence <= 0:
            self.turn_into_empty_node(events)
            return

        print(f" Defense Subsystem has {self.coherence} coherence left.")
        print(f" Defense Subsystem deals {self.strength} damage.")

        if self.player.shield:
            self.player.shield.block(events)
        else:
            player_coherence_loss = min(self.strength, self.player.coherence)
            self.player.coherence -= player_coherence_loss
            print(f" Virus now has {self.player.coherence} coherence.")
            events.append(("player_coherence_loss", player_coherence_loss))

        if self.player.coherence <= 0:
            self.player.finished = True
            print(f"\n\nSYSTEM HACK FAILED\n")
            fade_out_and_exit(root)

    def turn_into_empty_node(self, events):
        """
        Turns the node into an 'empty node'.
        (It removes the encounter.)

        Also removes the defense from the list of defense instances.
        """
        super().turn_into_empty_node(events)
        print(f"{self.type} is no more.")
        if not isinstance(self, Core):
            Defense.instances.remove(
                self
            )  # Tracks non-core defense nodes only, core won't be in it


class Core(Defense):
    TYPE = "System Core"
    IMAGE_KEY = "Core"
    COHERENCE = 90
    STRENGTH = 10
    TITLE = "System Core"
    BODY = "Destroying the System Core successfully completes your hacking attempt. You can attack the System Core by left clicking it."


class Firewall(Defense):
    TYPE = "Firewall"
    IMAGE_KEY = "Firewall"
    COHERENCE = 80
    STRENGTH = 20
    TITLE = "Defense Subsystem: Firewall"
    BODY = "The Firewall is a standard piece of system defense known for its high coherence. You can attack the Firewall by left clicking it."


class Restoration(Defense):
    TYPE = "Restoration Node"
    IMAGE_KEY = "Restorer"
    COHERENCE = 80
    STRENGTH = 10
    POWER = 20
    TITLE = "Defense Subsystem: Restoration Node"
    BODY = "While the Restoration Node subsystem is active, it will restore coherency to other uncovered Defense Subsystems. You can attack the Restoration Node by left clicking it."

    def restore_defense_nodes(events):
        """
        Heals random defense nodes for each active Restoration Node.
        The Restoration Nodes won't self-heal.
        """
        restoration_count = sum(
            isinstance(defense, Restoration) for defense in Defense.instances
        )

        if restoration_count > 0:
            if len(Defense.instances) > 1:
                for defense in Defense.instances:
                    if isinstance(defense, Restoration):
                        restoration_targets = Defense.instances.copy()
                        restoration_targets.remove(defense)
                        defense_to_be_restored = random.choice(restoration_targets)
                        print(
                            f"A Restoration Node adds {defense.power} coherence to the defensive node at {defense_to_be_restored.node.row},{defense_to_be_restored.node.column}"
                        )
                        defense_to_be_restored.coherence += Restoration.POWER
                        defense_node = defense_to_be_restored.node
                        events.append(
                            ("node_coherence_loss", defense_node, (-Restoration.POWER))
                        )


class Antivirus(Defense):
    TYPE = "Antivirus"
    IMAGE_KEY = "Antivirus"
    COHERENCE = 60
    STRENGTH = 40
    TITLE = "Defense Subsystem: Anti-Virus"
    BODY = "The Anti-Virus is a standard piece of system defense known for its high strength. You can attack the Anti-Virus by left clicking it."


class Suppressor(Defense):
    TYPE = "Suppressor"
    IMAGE_KEY = "Suppressor"
    COHERENCE = 60
    STRENGTH = 15
    POWER = 15
    TITLE = "Defense Subsystem: Virus Suppressor"
    BODY = "While the Virus Suppressor defense subsystem is active, your virus strength is reduced. You can attack the Virus Suppressor by left clicking it."

    def update_suppressed_strength(self, events):
        """
        Returns number of by how much player strength was reduced by Suppressors.
        (Strength cannot be reduced below 10).
        """
        min_strength_value = 10
        suppressor_strength = Suppressor.ability_power(self)
        suppressor_count = sum(
            isinstance(defense, Suppressor) for defense in Defense.instances
        )
        previous_suppressed_strength = self.player.suppressed_strength
        suppressed_strength = max(
            min_strength_value,
            (self.player.strength - suppressor_strength * suppressor_count),
        )

        self.player.suppressed_strength = suppressed_strength
        reduced = previous_suppressed_strength - suppressed_strength
        events.append(("player_strength_loss", reduced))
        return reduced

    def turn_into_empty_node(self, events):
        """
        Turns the node into an 'empty node'.
        (It removes the encounter.)

        Specific to the Suppressor this also updates suppressed strength as the Suppressor dies.
        """
        super().turn_into_empty_node(events)
        increased = -self.update_suppressed_strength(events)
        print(f"With the Virus Suppressor gone your strength recovers by {increased}.")


class Shield(Utility):
    TYPE = "Polymorphic Shield"
    IMAGE_KEY = "Shield"
    TOOL_IMAGE_KEY = "Tool Shield"
    TOOL_TITLE = "Utility Subsystem: Polymorphic Shield"
    TOOL_BODY = (
        "Polymorphic Shield protects the Virus from 2 attacks. Left click to activate."
    )
    CHARGES = 2

    def block(self, events):
        if self.charges > 0:
            self.charges -= 1
            print(f" Attack blocked! {self.charges} shield left.")
            events.append(("slot_update", self.slot))
            if self.charges == 0:
                print("Polymorphic shield is done and disappears.")
                self.turn_into_empty_slot()
                self.player.shield = None

    def activate(self, events):
        # TODO: Check this. Not sure if using a second self shield is blocked by using a first, if it stacks or overrides.
        # Implementing it as if an active one is blocking the next.
        if self.player.shield:
            print("Player is already shielded!")
        elif not self.activated:
            self.activated = True
            self.player.shield = self
            print(f"Activating {self.type}!")
        else:
            print(f"{self.type} is already activated!")


class Vector(Utility):
    TYPE = "Secondary Vector"
    IMAGE_KEY = "Vector"
    TOOL_IMAGE_KEY = "Tool Vector"
    TOOL_TITLE = "Utility Subsystem: Secondary Vector"
    TOOL_BODY = "Secondary Vector reduces the coherence of a Defense Subsystem or System Core by 20 over 3 turns. Left click to use and left click on the intended target."
    CHARGES = 3
    POWER = 20

    def reduce(self, node, events):
        if self.charges > 0 and node.encounter:
            reduce_amount = self.power
            print(
                f"Secondary Vector reduces the {node.encounter.type} coherence by {reduce_amount}"
            )
            node.encounter.coherence -= reduce_amount
            if node.encounter.coherence <= 0:
                print(f"{node.encounter.type} is destroyed by Secondary Vector.")
                node.encounter.turn_into_empty_node(events)
                self.turn_into_empty_slot()
            events.append(("node_coherence_loss", node, reduce_amount))
            events.append(("slot_update", self.slot))
            events.append(("node_update", node))
            self.charges -= 1
            if self.charges == 0:
                if node.encounter:
                    self.target_node = None
                    print(f"{node.encounter.type} survives the Secondary Vector.")
                print("Secondary Vector is done and disappears.")
                self.turn_into_empty_slot()
        else:
            print("Secondary Vector's effect is no longer relevant and expires.")
            events.append(("slot_update", self.slot))
            self.turn_into_empty_slot()

    def affect_target(self, node, events):
        self.player.target_selection = None
        self.activated = True
        print(f"The {node.encounter.type}'s coherence is affected by Secondary Vector.")
        self.reduce(node, events)
        self.target_node = node

    def activate(self, events):
        if not self.activated:
            if not self.targeting:
                if self.player.target_selection:
                    print(
                        f"You were already targeting for another {self.player.target_selection.type}. Switching!"
                    )
                    self.player.target_selection.targeting = False
                self.targeting = True
                self.player.target_selection = self
                print(f"Activating {self.type}!")
            else:
                print("You are already looking for a target.")
        else:
            print(f"{self.type} is already activated!")


class Rot(Utility):
    TYPE = "Kernel Rot"
    IMAGE_KEY = "Rot"
    TOOL_IMAGE_KEY = "Tool Rot"
    TOOL_TITLE = "Utility Subsystem: Kernel Rot"
    TOOL_BODY = "Kernel Rot halves the coherence of a Defense Subsystem or System Core. Left click to use and left click on the intended target."

    def affect_target(self, node, events):
        self.player.target_selection = None
        coherence = node.encounter.coherence
        # TODO: Check this. Should this be rounded up or down? Rounding down for now.
        reduced_coherence = coherence // 2
        node.encounter.coherence -= reduced_coherence
        events.append(("node_coherence_loss", node, reduced_coherence))
        events.append(("slot_update", self.slot))
        events.append(("node_update", node))
        print(f"The {node.encounter.type}'s coherence is halved by Kernel Rot.")
        self.turn_into_empty_slot()

    def activate(self, events):
        if not self.activated:
            if not self.targeting:
                if self.player.target_selection:
                    print(
                        f"You were already targeting for another {self.player.target_selection.type}. Switching!"
                    )
                    self.player.target_selection.targeting = False
                self.targeting = True
                self.player.target_selection = self
                print(f"Activating {self.type}!")
            else:
                print("You are already looking for a target.")
        else:
            print(f"{self.type} is already activated!")


class Repair(Utility):
    TYPE = "Self Repair"
    IMAGE_KEY = "Repair"
    TOOL_IMAGE_KEY = "Tool Repair"
    TOOL_TITLE = "Utility Subsystem: Self Repair"
    CHARGES = 3

    def __init__(self, player, node=None):
        super().__init__(player, node)
        # TODO: Check this. Repair values of 5 and 17 are the lowest and highest random values I saw (among 5, 6, 7, 8, 9, 10, 16, 17)
        # I'm not entirely sure of this distribution, it might have a larger range or be affected by difficulty somehow?
        # It could also be weighted, higher values seem rare. Using an even distribution between min and max for now.
        self.power = random.randint(5, 17)
        self.tool_body = f"Self Repair increases the Virus coherence when used by {self.power} per turn for 3 turns. Left click to use."

    def repair(self, events):
        if self.charges > 0:
            repair_amount = self.power
            print(f"Self Repair adds {repair_amount} coherence.")
            self.player.coherence += repair_amount
            events.append(("player_coherence_loss", (-repair_amount)))
            self.charges -= 1
            events.append(("slot_update", self.slot))
            if self.charges == 0:
                print("Self Repair is done and disappears.")
                self.turn_into_empty_slot()

    def activate(self, events):
        # TODO: Check this. Not sure if using a second self repair is blocked by using a first, if it stacks or overrides.
        # Implementing it for now as if I can use them all and they stack.
        if not self.activated:
            self.repair(events)
            self.activated = True
            print(f"Activating {self.type}!")
        else:
            print(f"{self.type} is already activated!")


DEFENSES = [Firewall, Antivirus, Restoration, Suppressor]
UTILITIES = [Repair, Shield, Rot, Vector]


class Player(object):
    """
    The Virus, you. Keeps track of the player stats.
    """

    def __init__(self, coherence: int, strength: int, utility_element_slots: int = 3):
        self.coherence = coherence
        self.strength = strength
        self.suppressed_strength = strength
        self.utility_element_slots = utility_element_slots
        self.utilities = [None] * utility_element_slots
        self.shield = None
        self.target_selection = None
        self.finished = False

    def add_utility(self, utility: Utility):
        """
        Returns True if utility can be added, False if not.
        """
        for slot in range(len(self.utilities)):
            if self.utilities[slot] is None:
                self.utilities[slot] = utility
                utility.slot = slot
                print(f"Added {utility.type}.")
                return True
        print(f"Failed to add {utility.type}, slots are full.")
        return False


class Engine(object):
    """
    The Engine does the calculations, the logic. It handles the invisible actions.

    The visible parts will be rendered by the board.
    """

    def __init__(self, player: Player):
        self.width = BOARD_WIDTH
        self.height = BOARD_HEIGHT
        self.nodes = []
        self.core = None
        self.start_node = None
        self.player = player
        self.events = []
        self.turn = 0

    def create_nodes(self):
        """
        Sets up a grid of nodes with random shape,
        with random start, core and encounter node locations.
        """

        for row in range(self.height):
            self.nodes.append([None] * self.width)
            for column in range(self.width):
                self.nodes[row][column] = Node(row, column)
        self.remove_random_nodes()

        # Ensure that the starting node is not on a small island,
        # which can exist because of the random removal of nodes
        while True:
            self.create_start_node()
            self.reset_distances()
            self.start_node.distance = 0

            # Picking a dynamic threshold that should not be too small (increased tiny island risk)
            # and also not too big (endless loop)
            threshold = (self.width + self.height) // 3
            self.set_distances(threshold)
            max_distance = max(
                node.distance for node in self.iter_nodes() if node.distance is not None
            )
            if max_distance >= threshold:
                # Good enough! Let's pick this location
                break

        # Remove the disconnected islands
        for node in self.iter_nodes():
            if node.distance is None:
                node.removed = True

        # Distribute the rest of the landmarks
        self.create_core()
        self.distribute_encounters()

    def remove_random_nodes(self):
        """
        Removes a random selection of nodes.
        """
        for _ in range(self.width * self.height // (FRACTION_REMOVED)):
            row = random.choice(self.nodes)
            node = random.choice(row)
            node.removed = True

    def create_start_node(self):
        """
        Sets a random existing node as the new start node.
        """

        self.reset_start_node()
        while True:
            start_row = random.choice(self.nodes)
            start_node = random.choice(start_row)
            if not start_node.removed:
                start_node.is_start = True
                self.start_node = start_node
                break

    def reset_start_node(self):
        for node in self.iter_nodes():
            node.is_start = False

    def create_core(self):
        """
        The core is at least 7 steps away from start if possible, otherwise in any random spot.

        (This last condition is what causes the regular "I found the core at first step!" posts)
        """
        self.reset_distances()
        self.start_node.distance = 0
        self.set_distances(7)

        any_core_options = [
            node
            for node in self.iter_nodes()
            if not node.removed and node.distance != 0
        ]
        far_core_options = [node for node in any_core_options if node.distance > 6]
        # Too easy if there are fewer than 3 viable options. Not sure if EVE also has such a check or if 1 viable option is enough there.
        core_options = (
            far_core_options if len(far_core_options) > 3 else any_core_options
        )
        self.core = random.choice(core_options)
        self.core.is_core = True
        self.core.encounter = Core(self.player, self.core)

    def distribute_encounters(self):
        """
        Spreads encounters randomly across the available nodes, based on the values defined in:
        - FRACTION_DEFENSE
        - FRACTION_UTILITY
        - FRACTION_CACHE
        """

        valid_nodes = [
            node
            for node in self.iter_nodes()
            if not node.removed and not node.is_start and not node.is_core
        ]
        random.shuffle(valid_nodes)

        # Calculate how many nodes of each type spawn
        defenses = math.ceil(len(valid_nodes) / FRACTION_DEFENSE)
        utilities = math.ceil(len(valid_nodes) / FRACTION_UTILITY)
        caches = math.ceil(len(valid_nodes) / FRACTION_CACHE)

        # Place defenses according to 'rule of 6': defense never spawns when surrounded by 6 nodes
        valid_defense_nodes = [
            node for node in valid_nodes if len(self.get_neighbours(node)) < 6
        ]
        random.shuffle(valid_defense_nodes)

        for node in valid_defense_nodes[:defenses]:
            valid_nodes.remove(node)
            defense = random.choice(DEFENSES)
            node.encounter = defense(self.player, node)

        # Also place one more defense node next to the core if possible
        # This is the special case that doesn't adhere to 'rule of 6':
        # a defense surrounded by 6 is next to the core
        core_neighbours = set(self.get_neighbours(self.core))
        valid_set = set(valid_nodes)
        candidates = list(core_neighbours & valid_set)
        if candidates:
            node = random.choice(candidates)
            valid_nodes.remove(node)
            defense = random.choice(DEFENSES)
            node.encounter = defense(self.player, node)

        # Randomly place utilities
        for node in valid_nodes[:utilities]:
            node = valid_nodes.pop()
            node.encounter = Shield(node)
            utility = random.choice(UTILITIES)
            node.encounter = utility(self.player, node)

        # And data caches
        for node in valid_nodes[:caches]:
            node = valid_nodes.pop()
            node.encounter = DataCache(self.player, node)

    def get_neighbours(self, center_node: Node):
        """
        Returns a list of all existing neighbours of the node in the hexagonal grid.
        """

        # Neighbouring node directions are different depending on even or odd rows
        if center_node.row % 2 == 0:
            directions = [(-1, -1), (-1, 0), (0, -1), (0, 1), (1, -1), (1, 0)]
        else:
            directions = [(-1, 0), (-1, 1), (0, -1), (0, 1), (1, 0), (1, 1)]
        neighbours = []
        # Check if the nodes are within bounds and not removed
        for dr, dc in directions:
            row = center_node.row + dr
            column = center_node.column + dc
            if 0 <= row < self.height and 0 <= column < self.width:
                node = self.nodes[row][column]
                if node is not None and not node.removed:
                    neighbours.append(node)
        return neighbours

    def set_distances(self, max_value: int = 10):
        """
        Sets distance of each node to the nearest node(s) that have already been defined to have 'distance = 0'.

        This is used to find the distance of the core to the start,
        as well as the distance to the nearest core/utility/datacache while playing.
        """

        for i in range(self.width * self.height):
            changed = False
            for node in self.iter_nodes():
                if node is None or node.removed:
                    continue
                if node.distance == i or node.distance == max_value:
                    neighbours = self.get_neighbours(node)
                    for neighbour in neighbours:
                        if (
                            neighbour
                            and not neighbour.removed
                            and neighbour.distance is None
                        ):
                            neighbour.distance = min(i + 1, max_value)
                            changed = True
            if not changed:
                break

    def reset_distances(self):
        """
        Clears old distance results. Should be used before using defining new nodes at distance 0 and running set_distances
        """

        for node in self.iter_nodes():
            node.distance = None

    def set_distances_to_good_stuff(self):
        """
        Sets distances to nearest unknown 'good node', i.e. core, data cache or utility node.

        Distances go up to 5 as that is how much info you get in EVE.
        """

        self.reset_distances()
        for node in self.iter_nodes():
            if not node.visited:
                if node.is_core:
                    node.distance = 0
                elif node.encounter:
                    if isinstance(node.encounter, Utility) or isinstance(
                        node.encounter, DataCache
                    ):
                        node.distance = 0
        self.set_distances(5)

    def iter_nodes(self):
        """
        Iterates over all nodes in the grid, makes looping over them easier.
        Yields nodes.
        """

        for row in self.nodes:
            for node in row:
                yield node

    def unlock_neighbours(self, node: Node):
        """
        Sets neighbouring nodes up for access. Returns a list of unlocked neighbours.

        Does not unblock: those nodes still need not to be blocked by defenses though before you can go there!
        """

        unlocked_neighbours = []
        for neighbour in self.get_neighbours(node):
            if not neighbour.can_be_visited and not neighbour.visited:
                neighbour.can_be_visited = True
                unlocked_neighbours.append(neighbour)
        return unlocked_neighbours

    def node_is_still_blocked(self, node: Node):
        """
        Return True if node is still blocked (by a neighbouring defense node).
        """

        blocked = False
        for neighbour in self.get_neighbours(node):
            if neighbour.visited and neighbour.encounter:
                if isinstance(neighbour.encounter, Defense) and not neighbour.is_core:
                    blocked = True
                    return blocked
        return blocked

    def block_neighbours(self, node: Node):
        """
        Sets neighbouring nodes to blocked.
        """

        for node in self.get_neighbours(node):
            node.blocked = True

    def defense_died(self, node: Node):
        """
        Handles death of a defense node. Unblocks neighbouring nodes if no longer blocked, wins game if core died.
        """
        self.events.append(("node_update", node))
        self.events.append(("line_update", node))

        if node.is_core:
            self.player.finished = True
            print("\n\nSYSTEM HACK SUCCESSFUL\n\nHere is a carbon.\n")
            fade_out_and_exit(root, success=True)
        else:
            print("Destroying the defensive node clears the blockade.")
            for neighbour in self.get_neighbours(node):
                neighbour.blocked = self.node_is_still_blocked(neighbour)
                self.events.append(("node_update", neighbour))

    def visit(self, node: Node):
        """
        'Visit' handles the first interaction with a new node:
        - unlocking neighbouring nodes
        - blocking surrounding nodes if the node is a defense node
        - updating distances to the next 'good nodes' if the node is a good node
        """

        node.visited = True
        node.can_be_visited = False
        self.unlock_neighbours(node)

        # Visiting an empty node
        if not node.encounter:
            node.empty = True
            if not node.is_start:
                print("Found an empty node.")

        # Visiting a non-core defense node that blocks surrounding nodes
        elif (
            node.encounter and isinstance(node.encounter, Defense) and not node.is_core
        ):  # Visited a blocking non-core defense node
            print(
                f"Uh-oh! You encountered a {node.encounter.type} at {node.row},{node.column}"
            )
            Defense.instances.append(node.encounter)
            self.block_neighbours(node)
            if isinstance(node.encounter, Suppressor):
                reduced = Suppressor.update_suppressed_strength(
                    node.encounter, self.events
                )
                print(f"The Virus Suppressor reduces your strength by {reduced}.")

        # Visiting one of the good nodes the numbered path points towards
        elif node.encounter and (
            isinstance(node.encounter, Utility)
            or isinstance(node.encounter, DataCache)
            or node.is_core
        ):
            if node.is_core:
                print(f"You found the Core!")
            else:
                print(f"You found a {node.encounter.type} at {node.row},{node.column}")
            self.set_distances_to_good_stuff()

    def initialize(self):
        """
        Initializes the nodes, by setting up the start node and the path to the good nodes.
        """

        self.visit(self.start_node)
        self.set_distances_to_good_stuff()

    def new_turn(self):
        """
        Triggers turn-based actions, such as Restoration Node repairs, Self Repairs and Secondary Vectors.
        """
        if not self.player.finished:
            for utility in self.player.utilities:
                if utility:
                    if utility.activated and utility.type == "Self Repair":
                        utility.repair(self.events)
                    elif utility.activated and utility.type == "Secondary Vector":
                        defense_node = utility.target_node
                        utility.reduce(utility.target_node, self.events)
                        if not defense_node.encounter:
                            self.defense_died(utility.target_node)

            # TODO: Check this. Here I make the assumption Restoration happens after Secondary Vectors.
            # I do not know if that is true. If I get evidence for the contrary I'll swap.
            # This does make it less likely that Restoration spoils a well-calculated Vector kill.
            Restoration.restore_defense_nodes(self.events)

            self.turn += 1

    def on_node_click(self, node: Node):
        """
        Handles all actions that need to be happening when a player interacts with a node.
        Returns False if node click was target selection for utility.
        Returns True if the usual node interaction happened.
        """

        if self.target_mode(node):
            return False
        else:
            # The usual interaction with a node
            if node.visited and not node.empty:
                if node.encounter and isinstance(node.encounter, Defense):
                    print(
                        f"Attacking the {node.encounter.type} at {node.row},{node.column}."
                    )
                    node.encounter.interact(self.events)
                    if node.empty:
                        self.defense_died(node)

                if node.encounter and isinstance(node.encounter, Utility):
                    utility_added = node.encounter.interact(self.events)
                    if not utility_added:
                        # The toolbelt is full so this does not work. Skip this click.
                        return

                if node.encounter and isinstance(node.encounter, DataCache):
                    print("What? Data Cache is evolving!")
                    node.encounter = node.encounter.interact(self.events)
                    print(
                        f"Congratulations! Your Data Cache evolved into {node.encounter.type}!"
                    )

                    if isinstance(node.encounter, Defense):
                        Defense.instances.append(node.encounter)
                        self.block_neighbours(node)

                        if isinstance(node.encounter, Suppressor):
                            reduced = Suppressor.update_suppressed_strength(
                                node.encounter, self.events
                            )
                            print(
                                f"The newly evolved Virus Suppressor reduces your strength by {reduced}."
                            )
                self.new_turn()

            if node.can_be_visited:
                self.visit(node)
                self.new_turn()
        return True

    def target_mode(self, node: Node):
        """
        Checks if player is using a utility tool to target.
        Returns True if yes, False if not targeting.

        If the target is a defense node, affect it with the utility tool.
        """
        targeting = False
        if self.player.target_selection:
            targeting = True
            if node.visited and node.encounter:
                if isinstance(node.encounter, Defense):
                    print(f"Targeting a {node.encounter.type}.")
                    self.player.target_selection.affect_target(node, self.events)
                    if not node.encounter:
                        self.defense_died(node)
                else:
                    print("Wrong target.")
                    self.player.target_selection.targeting = False
                    self.player.target_selection = None
            else:
                print("Wrong target.")
                self.player.target_selection.targeting = False
                self.player.target_selection = None
        return targeting


class Board(object):
    """
    The Board contains everything needed to render the board, the buttons, the layout, the labels and things you see while playing.
    """

    def __init__(self, nodes: list[Node], engine: Engine, player: Player):
        self.nodes = nodes
        self.engine = engine
        self.player = player
        self.buttons = {}
        self.lines = {}
        self.utility_buttons = {}
        self.utility_charges = {}
        self.utility_tooltip = None
        self.tooltip_after_ids = []
        self.stats = None
        self.tooltip_title, self.tooltip_body = self.create_grid_tooltips()

    def get_screen_position(self, node: Node, location: str = None):
        """
        Returns the position of the node within the hexagonal grid in x and y coordinates.

        Takes location inputs like 'center' 'above' or 'below' for positions relative to where the button of the node is rendered.
        """
        if location == "center":
            center_shift = BUTTON_SIZE / 2
        else:
            center_shift = 0
        if location == "above":
            above_shift_up = BUTTON_SIZE / 2 - 5
            above_shift_side = BUTTON_SIZE / 4 + 6
        elif location == "below":
            above_shift_up = -BUTTON_SIZE / 2 - 25
            above_shift_side = BUTTON_SIZE / 4 + 6
        else:
            above_shift_up = 0
            above_shift_side = 0
        x = (
            node.column * (BUTTON_SIZE + X_SPACING)
            + ((BUTTON_SIZE + X_SPACING) / 2 if node.row % 2 else 0)
            + center_shift
            + PADDING
            + above_shift_side
        )
        y = node.row * Y_SPACING + center_shift + PADDING - above_shift_up
        return x, y

    def on_grid_button_click(self, node: Node):
        """
        Handles everything that needs to be done whenever one of the buttons of the grid is clicked:
        Activates the Engine (on_node_click), updates images, lines, numbers and handles events for damage numbers.
        """

        # Disables buttons when game is finished
        if self.player.finished:
            return

        interact_with_utilities = True if isinstance(node.encounter, Utility) else False

        if self.engine.on_node_click(node):

            for neighbour in self.engine.get_neighbours(node):
                self.update_grid_button(neighbour)
            self.update_lines(node)

            if (
                interact_with_utilities and not node.encounter
            ):  # Consumed a utility node
                for slot in range(self.player.utility_element_slots):
                    self.update_utility_element(slot)

        self.handle_events()
        self.update_grid_button(
            node
        )  # Update this button last to ensure correct tooltip shows

    def create_grid_buttons(self):
        """
        Creates all the buttons of the hexagonal grid.
        """

        for node in self.engine.iter_nodes():
            if node.removed:
                continue
            else:
                x, y = self.get_screen_position(node)
                button = tkinter.Button(
                    root,
                    fg="white",
                    compound="center",
                    font=("Arial", 8, "bold"),
                    relief="flat",
                    borderwidth=0,
                    highlightthickness=0,
                    bg=HEX,
                    activebackground=HEX,
                )
                button.place(x=x, y=y, width=BUTTON_SIZE, height=BUTTON_SIZE)
                self.buttons[node] = button
                self.update_grid_tooltips(node)
                self.update_grid_button(node)

    def update_grid_button(self, node: Node):
        """
        Updates existing buttons of the hexagonal grid. Changes in image, blocked status and text are done here.
        """

        if not node.shown_path:
            button = self.buttons[node]
            command = lambda n=node: self.on_grid_button_click(n)
            image = IMAGES["Unexplored"]
            text = ""
            bg = HEX

            if node.blocked:
                state = "disabled"
            else:
                state = "normal"

            if node.empty and node.visited:
                image = IMAGES["Empty"]
                if not node.is_start:
                    command = lambda: None
                    if node.distance:
                        text = f"{node.distance}"
                    else:
                        text = "5"
                    path_message_duration = 1500
                    root.after(path_message_duration, lambda: button.config(text=""))
                    node.shown_path = True
            elif node.can_be_visited:
                image = IMAGES["Encrypted"]
            elif node.visited and node.encounter:
                image = node.encounter.image
                if isinstance(node.encounter, Defense):
                    text = (
                        f"✶{node.encounter.coherence}\n\n\nᯤ{node.encounter.strength}"
                    )
            button.config(image=image, text=text, state=state, command=command, bg=bg)
            self.update_grid_tooltips(node)

    def create_player(self):
        """
        Creates the image bottom left with player stats and adds text with starting health and coherence.
        """

        stats_y = self.engine.height * Y_SPACING + PADDING * 1.5
        stats_x = PADDING - 30
        stats = tkinter.Label(
            root,
            image=IMAGES["Stats"],
            text=f"✶{self.player.coherence}\n\n\n\n\nᯤ{self.player.suppressed_strength}",
            compound="center",
            fg="white",
            font=("Arial", 8),
            borderwidth=0,
            highlightthickness=0,
            bg=HEX,
            activebackground=HEX,
        )
        stats.place(x=stats_x, y=stats_y)
        self.stats = stats

    def update_player(self):
        """
        Updates the text showing player health and coherence.
        """

        text = f"✶{self.player.coherence}\n\n\n\n\nᯤ{self.player.suppressed_strength}"
        self.stats.config(text=text)

    def create_grid_tooltips(self):
        """
        Creates the tooltip bottom right that is used for mouseover text of the node buttons.
        """

        tooltip_width = 300
        tooltip_height = 130
        tooltip_y = self.engine.height * Y_SPACING + PADDING * 1.5 - 25
        tooltip_x = (
            self.engine.width * (BUTTON_SIZE + X_SPACING) + PADDING - tooltip_width + 30
        )
        tooltip_frame = tkinter.Frame(root, bg=HEX, relief="solid")
        tooltip_frame.place(
            x=tooltip_x, y=tooltip_y, width=tooltip_width, height=tooltip_height
        )
        inner_frame = tkinter.Frame(tooltip_frame, bg=HEX)
        inner_frame.pack(side="bottom", anchor="se", fill="x")
        tooltip_title = tkinter.Label(
            inner_frame,
            text="",
            bg=HEX,
            fg="white",
            font=("Arial", 12, "bold"),
            anchor="e",
            justify="right",
            wraplength=255,
        )
        tooltip_title.pack(fill="x")
        tooltip_body = tkinter.Label(
            inner_frame,
            text="",
            bg=HEX,
            fg="grey",
            font=(
                "Arial",
                10,
            ),
            anchor="e",
            justify="right",
            wraplength=255,
        )
        tooltip_body.pack(fill="both", expand=True)
        return tooltip_title, tooltip_body

    def update_grid_tooltips(self, node: Node):
        """
        Updates the text of the tooltip bottom right that is used for mouseover text of the node buttons.
        """

        title_text = ""
        body_text = ""
        if not (node.can_be_visited or node.visited):
            pass
        elif node.can_be_visited and not node.visited:
            title_text = "Encrypted Node"
            body_text = "Reveal Encrypted Node until you reach the System Core. Left click to decrypt the node and reveal the contents."
        elif node.encounter:
            title_text = node.encounter.title
            body_text = node.encounter.body
        elif node.visited:
            title_text = "Empty Node"
            body_text = "This node has been revealed and is empty. It currently serves as a connector, letting you reveal all encrypted nodes which are adjacent by left clicking them."

        def on_enter(event):
            self.tooltip_title.config(text=title_text)
            self.tooltip_body.config(text=body_text)

        button = self.buttons[node]
        button.bind("<Enter>", on_enter)

        # Also refresh the tooltip to match the button that has just been clicked
        self.tooltip_title.config(text=title_text)
        self.tooltip_body.config(text=body_text)

    def create_utility_buttons(self):
        """
        Creates the utility slots at the bottom of the screen, as well as the label for the charge amounts.
        """

        # TODO: Also add activate images for better visual response on clicking, matching EVE.
        # TODO: And also a fade out / fade in effect for activated utilities.
        utilities_y = self.engine.height * Y_SPACING + PADDING * 1.5 + 48
        utilities_x = (self.engine.width * (BUTTON_SIZE + X_SPACING)) // 2 - 160
        for slot in range(self.player.utility_element_slots):
            image = IMAGES["Tool Empty"]
            utilities_x += BUTTON_SIZE + 15
            button = tkinter.Button(
                root,
                compound="center",
                image=image,
                relief="flat",
                borderwidth=0,
                highlightthickness=0,
                bg=HEX,
                command=lambda slot=slot: self.on_utility_button_click(slot),
            )
            button.place(
                x=utilities_x, y=utilities_y, width=BUTTON_SIZE, height=BUTTON_SIZE
            )
            self.utility_buttons[slot] = button

            charge_label = tkinter.Label(
                text="", bg=HEX, fg="white", font=("Arial", 10, "bold")
            )
            charge_label.place(x=(utilities_x + 18), y=(utilities_y - 16))
            self.utility_charges[slot] = charge_label

            self.bind_utility_tooltip(slot)
            self.update_utility_element(slot)

        # Tooltip frame
        frame = tkinter.Frame(
            root,
            bg=HEX,
            relief="solid",
            highlightbackground="grey",
            highlightthickness=1,
            padx=15,
            pady=15,
        )
        title = tkinter.Label(
            frame,
            text="placeholder",
            bg=HEX,
            fg="white",
            font=("Arial", 12, "bold"),
            justify="left",
            wraplength=255,
        )
        title.pack(fill="both", expand=True)
        body = tkinter.Label(
            frame,
            text="more place",
            bg=HEX,
            fg="grey",
            font=(
                "Arial",
                10,
            ),
            justify="left",
            wraplength=255,
        )
        body.pack(fill="both", expand=True)
        self.utility_tooltip = {"frame": frame, "title": title, "body": body}

    def update_utility_element(self, slot: int):
        """
        Updates the utility slots at the bottom of the screen, as well as the label for the charge amounts.
        """

        # Hide old tooltip upon update
        if self.utility_tooltip:
            self.utility_tooltip["frame"].place_forget()

        if not self.player.utilities[slot]:
            image = IMAGES["Tool Empty"]
            charges = 0
        else:
            utility = self.player.utilities[slot]
            image = IMAGES[utility.tool_image_key]
            charges = utility.charges
        self.utility_buttons[slot].config(image=image)

        if charges and charges > 0:
            charge_text = str(charges)
        else:
            charge_text = ""
        self.utility_charges[slot].config(text=charge_text)

    def bind_utility_tooltip(self, slot: int):
        """
        Binds mouseover tooltip to the utility button.
        """

        def on_enter(event, slot=slot):
            self.utility_buttons[slot].after(300, self.place_utility_tooltip(slot))

        def on_leave(event):
            self.utility_tooltip["frame"].place_forget()

        self.utility_buttons[slot].bind("<Enter>", on_enter)
        self.utility_buttons[slot].bind("<Leave>", on_leave)

    def place_utility_tooltip(self, slot: int):
        """
        Updates location and text of the utility tooltip and shows it
        """

        if self.player.utilities[slot]:
            utility = self.player.utilities[slot]
            title_text = utility.tool_title
            body_text = utility.tool_body
            tooltip = self.utility_tooltip
            tooltip_y = self.engine.height * Y_SPACING + PADDING * 1.5 + 40
            tooltip_x = (
                (self.engine.width * (BUTTON_SIZE + X_SPACING)) // 2
                - 70
                + (BUTTON_SIZE + 15) * slot
            )
            tooltip["title"].config(text=title_text)
            tooltip["body"].config(text=body_text)
            tooltip["frame"].lift()
            tooltip["frame"].place_configure(x=tooltip_x, y=tooltip_y, anchor="s")

    def on_utility_button_click(self, slot: int):
        """
        Handles everything that needs to be done whenever a utility button is clicked.
        """

        if self.player.utilities[slot]:
            self.player.utilities[slot].activate(self.engine.events)
        else:
            print("This slot is empty.")
        self.handle_events()

    def handle_events(self):
        """
        Handles events from the encounters and engine to do board changes.
        """

        for event in self.engine.events:
            if event[0] == "player_coherence_loss":
                _, amount = event
                self.show_value_change(player=True, amount=-amount, type="Coherence")
                self.update_player()
            elif event[0] == "node_coherence_loss":
                _, node, amount = event
                self.show_value_change(node=node, amount=-amount, type="Coherence")
                if (
                    amount < 0
                ):  # Restoration heal to a random node possibly outside current target and surrounding nodes (which get updated already).
                    self.update_grid_button(node)
            elif event[0] == "player_strength_loss":
                _, amount = event
                self.show_value_change(player=True, amount=-amount, type="Strength")
                self.update_player()
            elif event[0] == "node_strength_loss":
                # Not in use in EVE yet but could be fun for custom additions
                _, node, amount = event
                self.show_value_change(node=node, amount=-amount, type="Strength")
                self.update_grid_button(node)
            elif event[0] == "slot_update":
                _, slot = event
                self.update_utility_element(slot)
            elif event[0] == "node_update":
                _, node = event
                self.update_grid_button(node)
            elif event[0] == "line_update":
                _, node = event
                self.update_lines(node)
            else:
                warnings.warn(f"Unknown event: {event}")
        self.engine.events.clear()
        pass

    def show_value_change(
        self, amount: int, type: str, node: Node = None, player: Player = False
    ):
        """
        Shows temporary numbers for coherence and strength changes of players or nodes.
        """

        # Adds a + in front of positive numbers
        change = str(amount) if amount < 0 else f"+{amount}"
        message_duration = 400
        temp_label = tkinter.Label(
            root, text=change, bg=HEX, fg="white", font=("Arial", 8)
        )
        x, y = 0, 0
        if node:
            if type == "Coherence":
                x, y = self.get_screen_position(node, location="above")
            elif type == "Strength":
                x, y = self.get_screen_position(node, location="below")
        elif player:
            x = PADDING + 29
            if type == "Coherence":
                y = self.engine.height * Y_SPACING + PADDING * 1.5 - 10
            elif type == "Strength":
                y = self.engine.height * Y_SPACING + PADDING * 1.5 + 95
        temp_label.place(x=x, y=y)
        root.after(message_duration, temp_label.destroy)

    def create_lines(self):
        """
        Creates all lines of the hexagonal grid between the buttons, and initializes them grey.
        """

        grey = "#282828"
        for row in self.nodes:
            for node in row:
                if node.removed:
                    continue
                x1, y1 = self.get_screen_position(node, location="center")
                for neighbour in self.engine.get_neighbours(node):
                    if (neighbour.row > node.row) or (
                        neighbour.row == node.row and neighbour.column > node.column
                    ):
                        x2, y2 = self.get_screen_position(neighbour, location="center")
                        line = canvas.create_line(
                            x1, y1, x2, y2, fill=grey, width=2, capstyle="round"
                        )
                        self.lines[(node, neighbour)] = line

    def update_lines(self, node: Node):
        """
        Updates the colours of lines around the node and it's neighbouring nodes to match blocked (black), travelled (orange) and open (cyan) paths.
        """

        # Updates the colours of the lines around the node and it's neighbouring nodes
        orange = "#ac3e18"
        cyan = "#3A524E"
        black = "#000000"
        for neighbour in self.engine.get_neighbours(node):
            for (node1, node2), line in self.lines.items():
                if node1 is neighbour or node2 is neighbour:
                    if (
                        isinstance(node1.encounter, Defense)
                        and node1.visited
                        and not node1.is_core
                    ) or (
                        isinstance(node2.encounter, Defense)
                        and node2.visited
                        and not node2.is_core
                    ):
                        canvas.itemconfig(line, fill=black, width=8)
                    elif (
                        node1.blocked
                        and not node1.visited
                        or node2.blocked
                        and not node2.visited
                    ):
                        canvas.itemconfig(line, fill=black, width=8)
                    elif node1.visited and node2.visited:
                        canvas.itemconfig(line, fill=orange, width=3)
                    elif (
                        (node1.can_be_visited and not node1.blocked) or node1.empty
                    ) or ((node2.can_be_visited and not node2.blocked) or node2.empty):
                        canvas.itemconfig(line, fill=cyan, width=3)

    def render_board(self):
        """
        Creates the board and all it's elements: lines, buttons, player stats, utility elements, labels and credits.
        """

        self.create_lines()
        self.update_lines(self.engine.start_node)
        self.create_grid_buttons()
        self.create_player()
        self.create_utility_buttons()

        credit_text = "A simulation based on the original hacking minigame in EVE Online, by Gerard Amatin"
        credits = tkinter.Label(
            root, text=credit_text, bg=HEX, fg="grey", font=("Arial", 10)
        )
        credits.place(
            x=(self.engine.width * (BUTTON_SIZE + X_SPACING)) // 2 - 240,
            y=(self.engine.height * Y_SPACING + PADDING * 1.5 + 95),
        )
        print(credit_text)
        print("Click a node to start!")


def fade_out_and_exit(window: tkinter.Tk, alpha: float = 1.0, success: bool = False):
    """
    Shows a success or failure message based on 'success' and fades the screen before it closes, like in EVE.
    """

    if success:
        text = "SYSTEM HACK SUCCESSFUL"
    else:
        text = "SYSTEM HACK FAILED"

    label = tkinter.Label(
        root, text=text, font=("Arial", 24, "bold"), fg="white", bg=HEX
    )
    label_x = BOARD_WIDTH * (BUTTON_SIZE + X_SPACING) / 2 - 180
    label_y = BOARD_HEIGHT * (Y_SPACING) / 2 + 60
    label.place(x=label_x, y=label_y)

    if alpha > 0:
        alpha -= 0.05
        window.attributes("-alpha", alpha)
        window.after(100, fade_out_and_exit, window, alpha, success)
    else:
        window.destroy()
    pass


def main():
    player = Player(coherence=COHERENCE, strength=STRENGTH)

    engine = Engine(player)
    engine.create_nodes()
    engine.initialize()

    board = Board(engine.nodes, engine, player)
    board.render_board()

    window_width = engine.width * (BUTTON_SIZE + X_SPACING) + PADDING * 2
    window_height = engine.height * Y_SPACING + BOTTOM_SPACE + PADDING * 2
    root.geometry(f"{window_width}x{window_height}")
    root.config(bg=HEX)
    root.mainloop()


if __name__ == "__main__":
    main()
