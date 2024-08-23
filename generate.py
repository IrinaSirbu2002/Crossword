import sys

from crossword import *
from collections import deque


class CrosswordCreator():

    def __init__(self, crossword):
        """
        Create new CSP crossword generate.
        """
        self.crossword = crossword
        self.domains = {
            var: self.crossword.words.copy()
            for var in self.crossword.variables
        }

    def letter_grid(self, assignment):
        """
        Return 2D array representing a given assignment.
        """
        letters = [
            [None for _ in range(self.crossword.width)]
            for _ in range(self.crossword.height)
        ]
        for variable, word in assignment.items():
            direction = variable.direction
            for k in range(len(word)):
                i = variable.i + (k if direction == Variable.DOWN else 0)
                j = variable.j + (k if direction == Variable.ACROSS else 0)
                letters[i][j] = word[k]
        return letters

    def print(self, assignment):
        """
        Print crossword assignment to the terminal.
        """
        letters = self.letter_grid(assignment)
        for i in range(self.crossword.height):
            for j in range(self.crossword.width):
                if self.crossword.structure[i][j]:
                    print(letters[i][j] or " ", end="")
                else:
                    print("█", end="")
            print()

    def save(self, assignment, filename):
        """
        Save crossword assignment to an image file.
        """
        from PIL import Image, ImageDraw, ImageFont
        cell_size = 100
        cell_border = 2
        interior_size = cell_size - 2 * cell_border
        letters = self.letter_grid(assignment)

        # Create a blank canvas
        img = Image.new(
            "RGBA",
            (self.crossword.width * cell_size,
             self.crossword.height * cell_size),
            "black"
        )
        font = ImageFont.truetype("assets/fonts/OpenSans-Regular.ttf", 80)
        draw = ImageDraw.Draw(img)

        for i in range(self.crossword.height):
            for j in range(self.crossword.width):

                rect = [
                    (j * cell_size + cell_border,
                     i * cell_size + cell_border),
                    ((j + 1) * cell_size - cell_border,
                     (i + 1) * cell_size - cell_border)
                ]
                if self.crossword.structure[i][j]:
                    draw.rectangle(rect, fill="white")
                    if letters[i][j]:
                        _, _, w, h = draw.textbbox((0, 0), letters[i][j], font=font)
                        draw.text(
                            (rect[0][0] + ((interior_size - w) / 2),
                             rect[0][1] + ((interior_size - h) / 2) - 10),
                            letters[i][j], fill="black", font=font
                        )

        img.save(filename)

    def solve(self):
        """
        Enforce node and arc consistency, and then solve the CSP.
        """
        self.enforce_node_consistency()
        self.ac3()
        return self.backtrack(dict())

    def enforce_node_consistency(self):
        """
        Update `self.domains` such that each variable is node-consistent.
        (Remove any values that are inconsistent with a variable's unary
         constraints; in this case, the length of the word.)
        """
        for var in self.domains:
            to_remove = []
            for word in self.domains[var]:
                if var.length != len(word):
                    to_remove.append(word)
            for word in to_remove:
                self.domains[var].remove(word)

    def revise(self, x, y):
        """
        Make variable `x` arc consistent with variable `y`.
        To do so, remove values from `self.domains[x]` for which there is no
        possible corresponding value for `y` in `self.domains[y]`.

        Return True if a revision was made to the domain of `x`; return
        False if no revision was made.
        """
        overlap = self.crossword.overlaps[x, y]
        revise = []
        if overlap == None:
            return False
        for word_x in self.domains[x]:
            to_revise = True
            for word_y in self.domains[y]:
                if word_x[overlap[0]] == word_y[overlap[1]]:
                    to_revise = False
            if to_revise:
                revise.append(word_x)
        if revise:
            for word in revise:
                self.domains[x].remove(word)
        else:
            return False
        return True

    def ac3(self, arcs=None):
        """
        Update `self.domains` such that each variable is arc consistent.
        If `arcs` is None, begin with initial list of all arcs in the problem.
        Otherwise, use `arcs` as the initial list of arcs to make consistent.

        Return True if arc consistency is enforced and no domains are empty;
        return False if one or more domains end up empty.
        """
        if not arcs:
            # If arcs is None, start with an initial queue of all of the arcs in the problem.
            arcs = []
            for var in self.crossword.variables:
                for neighbor in self.crossword.neighbors(var):
                    arcs.append((var, neighbor))
        else:
            arcs = deque(arcs)
        while arcs:
            x, y = arcs.pop()
            if self.revise(x ,y):
                if len(self.domains[x]) == 0:
                    return False
                for z in self.crossword.neighbors(x) - {y}:
                    arcs.append((z, x))
        return True

    def assignment_complete(self, assignment):
        """
        Return True if `assignment` is complete (i.e., assigns a value to each
        crossword variable); return False otherwise.
        """
        for var in self.domains:
            if var not in assignment:
                return False
        return True
        
    def assignment_complete(self, assignment):
        """
        Return True if `assignment` is complete (i.e., assigns a value to each
        crossword variable); return False otherwise.
        """
        for var in self.domains:
            if var not in assignment:
                return False
        return True

    def consistent(self, assignment):
        """
        Return True if `assignment` is consistent (i.e., words fit in crossword
        puzzle without conflicting characters); return False otherwise.
        """
        distinct = []
        if assignment:

            # Check if there are distinct words
            for var in assignment:
                if assignment[var] in distinct:
                    return False
                if var.length != len(assignment[var]):
                    return False
                distinct.append(assignment[var])
            for var_x in assignment:
                for var_y in self.crossword.neighbors(var_x):
                    if var_y in assignment:
                        overlap = list(self.crossword.overlaps[var_x, var_y])
                        if assignment[var_x][overlap[0]] != assignment[var_y][overlap[1]]:
                            return False                           
            return True
        
    def assign_ruled_out_neighbors_to_words(self, word, var, assignment):
        count = 0
        for var_y in self.crossword.neighbors(var):
            overlap = self.crossword.overlaps[var, var_y]
            if var_y not in assignment:
                for word_y in self.domains[var_y]:
                    if word[overlap[0]] != word_y[overlap[1]]:
                        count += 1
        return count

    def order_domain_values(self, var, assignment):
        """
        Return a list of values in the domain of `var`, in order by
        the number of values they rule out for neighboring variables.
        The first value in the list, for example, should be the one
        that rules out the fewest values among the neighbors of `var`.
        """
        return sorted(self.domains[var], key=lambda word: self.assign_ruled_out_neighbors_to_words(word, var, assignment))
    
    def fewest_values_domain(self, assignment):
        fewest = 10000
        for var in self.domains:
            if var not in assignment:
                number = len(self.domains[var])
                if number < fewest:
                    fewest = number
        return fewest
    
    def largest_degree(self, vars):
        largest = 0
        for var in vars:
            neighbors = len(self.crossword.neighbors(var))
            if neighbors > largest:
                largest = neighbors
        return largest

    def select_unassigned_variable(self, assignment):
        """
        Return an unassigned variable not already part of `assignment`.
        Choose the variable with the minimum number of remaining values
        in its domain. If there is a tie, choose the variable with the highest
        degree. If there is a tie, any of the tied variables are acceptable
        return values.
        """
        few = []
        large = []
        fewest = self.fewest_values_domain(assignment) 
        for var in self.domains:
            if var not in assignment and len(self.domains[var]) == fewest:
                few.append(var)
        if len(few) == 1:
            return few[0]
        else:
            largest = self.largest_degree(few)
            for var in few:
                if len(self.crossword.neighbors(var)) == largest:
                    large.append(var)
        return large[0]
    
    def backtrack(self, assignment):
        """
        Using Backtracking Search, take as input a partial assignment for the
        crossword and return a complete assignment if possible to do so.

        `assignment` is a mapping from variables (keys) to words (values).

        If no assignment is possible, return None.
        """
        result = {}
        if self.assignment_complete(assignment):
            return assignment
        var = self.select_unassigned_variable(assignment)
        if self.ac3():
            for v in self.order_domain_values(var, assignment):
                assignment[var] = v
                if self.consistent(assignment):
                    result = self.backtrack(assignment)
                if result:
                    return result
                del assignment[var]
        return None

def main():

    # Check usage
    if len(sys.argv) not in [3, 4]:
        sys.exit("Usage: python generate.py structure words [output]")

    # Parse command-line arguments
    structure = sys.argv[1]
    words = sys.argv[2]
    output = sys.argv[3] if len(sys.argv) == 4 else None

    # Generate crossword
    crossword = Crossword(structure, words)
    creator = CrosswordCreator(crossword)
    assignment = creator.solve()

    # Print result
    if assignment is None:
        print("No solution.")
    else:
        creator.print(assignment)
        if output:
            creator.save(assignment, output)


if __name__ == "__main__":
    main()
