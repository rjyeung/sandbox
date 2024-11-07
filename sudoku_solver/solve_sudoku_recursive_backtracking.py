"""
This program uses recursive backtracking algorithm to solve any Sudoku.

Input:  A 2D list, with 0 marking empty spots in the Sudoku 
Output: If said sudoku is unsolvable, it will indicate so.  Otherwise,
        print out the final solution.        
 """

from pprint import pprint

def get_spot(puzzle):
    # i, j are row and column number in 9x9 sudoku
    # returns spot that has not yet been solved yet.
    # If all solved, return (None, None)
    for i in range(9):
        for j in range(9):
            if puzzle[i][j] == 0:
                return i, j
    return None, None

def print_puzzle(puzzle):
    # Print Sudoku board with a nicer format than pprint
    print_str = ''
    for i in range(9):
        if i in (3, 6):  # Print extra line in after row 3 and 6
            print_str += '\n'
        print_str += '\n'
        for j in range(9):
            if j%3 == 0:    # Print extra space after colum 0, 3, 6 before actual value
                print_str += ' '
            print_str += ' '+str(puzzle[i][j])
    print(print_str)

def verify_puzzle(puzzle, row, col, guess):
    # Check for guess is a valid choice for the spot
    row_values = puzzle[row]
    # print (f'Here with row_values {row_values}')
    if guess in row_values:
        return False

    # Check for guess is a valid choice for the column
    col_values = []
    for i in range(9):
        col_values.append(puzzle[i][col])
    # print (f'Here with col_values {col_values}')
    if guess in col_values:
        return False

    # Check for guess is a valid choice for the 3x3 box
    box_values=[]
    row_start = row//3 * 3
    col_start = col//3 * 3
    for x in range (row_start, row_start+3):
        box_values.extend(puzzle[x][col_start:col_start+3])
    if guess in box_values:
        return False  

    return True

def solve_sudoku(puzzle):
    # Step 1: Get an unsolved spot in sudoku
    row, col = get_spot(puzzle)
    # Step 3.1: If no more spot left, sudoku is solved.
    if row is None and col is None:
        return True

    # Step 2: Try all guesses for the spot
    for guess in range (1, 10):
        # Step 3: If guess seems valid, update puzzle, and call recursively.
        if verify_puzzle(puzzle, row, col, guess):
            puzzle[row][col] = guess
            if solve_sudoku(puzzle):
                return True

    # Step 4: When there is no valid solution for all guesses, backtrack to previous value.
    puzzle[row][col] = 0

    return False # Return False if none of the guesses work, puzzle is unsolvable. 


if __name__ == '__main__':
    #https://abcnews.go.com/blogs/headlines/2012/06/can-you-solve-the-hardest-ever-sudoku
    sudoku_puzzle = [
        [8, 0, 0,   0, 0, 0,   0, 0, 0],
        [0, 0, 3,   6, 0, 0,   0, 0, 0],
        [0, 7, 0,   0, 9, 0,   2, 0, 0],

        [0, 5, 0,   0, 0, 7,   0, 0, 0],
        [0, 0, 0,   0, 4, 5,   7, 0, 0],
        [0, 0, 0,   1, 0, 0,   0, 3, 0],

        [0, 0, 1,   0, 0, 0,   0, 6, 8],
        [0, 0, 8,   5, 0, 0,   0, 1, 0],
        [0, 9, 0,   0, 0, 0,   4, 0, 0]
    ]
    print('Sudoku to solve:')
    # pprint(sudoku_puzzle)
    print_puzzle(sudoku_puzzle)
    if not solve_sudoku(sudoku_puzzle):
        print('\n\nThis Sudoku is UNSOLVABLE.')
    print('\n\nSolution/Result:')
    # pprint(sudoku_puzzle)
    print_puzzle(sudoku_puzzle)