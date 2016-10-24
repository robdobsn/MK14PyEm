import tkinter as tk
from functools import partial

class SevenSegDigit:
    # Order 7 segments clockwise from top left, with crossbar last.
    # Coordinates of each segment are (x0, y0, x1, y1) 
    # given as offsets from top left measured in segment lengths.
    offsets = (
        (0, 0, 1, 0),  # top
        (1, 0, 1, 1),  # upper right
        (1, 1, 1, 2),  # lower right
        (0, 2, 1, 2),  # bottom
        (0, 1, 0, 2),  # lower left
        (0, 0, 0, 1),  # upper left
        (0, 1, 1, 1),  # middle
    )

    # Segments used for each digit; 0, 1 = off, on.
    digits = (
        (1, 1, 1, 1, 1, 1, 0),  # 0
        (0, 1, 1, 0, 0, 0, 0),  # 1
        (1, 1, 0, 1, 1, 0, 1),  # 2
        (1, 1, 1, 1, 0, 0, 1),  # 3
        (0, 1, 1, 0, 0, 1, 1),  # 4
        (1, 0, 1, 1, 0, 1, 1),  # 5
        (1, 0, 1, 1, 1, 1, 1),  # 6
        (1, 1, 1, 0, 0, 0, 0),  # 7
        (1, 1, 1, 1, 1, 1, 1),  # 8
        (1, 1, 1, 1, 0, 1, 1),  # 9
        (1, 1, 1, 0, 1, 1, 1),  # 10=A
        (0, 0, 1, 1, 1, 1, 1),  # 11=b
        (1, 0, 0, 1, 1, 1, 0),  # 12=C
        (0, 1, 1, 1, 1, 0, 1),  # 13=d
        (1, 0, 0, 1, 1, 1, 1),  # 14=E
        (1, 0, 0, 0, 1, 1, 1),  # 15=F
    )
    
    def __init__(self, canvas, *, x=10, y=10, length=20, width=3):
        self.canvas = canvas
        l = length
        self.segs = []
        for x0, y0, x1, y1 in self.offsets:
            self.segs.append(canvas.create_line(
                x + x0*l, y + y0*l, x + x1*l, y + y1*l,
                width=width, state = 'hidden'))

    def show(self, num):
        for iid, on in zip(self.segs, self.digits[num]):
            self.canvas.itemconfigure(iid, state = 'normal' if on else 'hidden')
    
class MK14_UI:

    def __init__(self, tkRoot):
        self.tkRoot = tkRoot

    def click(self, btn):
        # test the button command click
        s = "Button %s clicked" % btn
        self.tkRoot.title(s)
    
    def genButtons(self):
        # create a labeled frame for the keypad buttons
        # relief='groove' and labelanchor='nw' are default
        lf = tk.LabelFrame(self.tkRoot, text="", bd=3)
        lf.pack(padx=15, pady=10)
        # typical calculator button layout
        btn_list = [
        '7',  '8',  '9',  'A',  'B',   'C',
        '4',  '5',  '6',  'D',  'E',   'F',
        '1',  '2',  '3',   '', 'ABT',  'TRM',
        '',   '0',  '',    '', 'MEM',  'GO' ]
        # create and position all buttons with a for-loop
        # r, c used for row, column grid values
        r = 1
        c = 0
        n = 0
        # list(range()) needed for Python3
        btn = list(range(len(btn_list)))
        for label in btn_list:
            # partial takes care of function and argument
            cmd = partial(self.click, label)
            # create the button
            btn[n] = tk.Button(lf, text=label, width=5, command=cmd)
            # position the button
            btn[n].grid(row=r, column=c)
            # increment button index
            n += 1
            # update row/column position
            c += 1
            if c > 5:
                c = 0
                r += 1

    def genDigits(self, numDigits):
        screen = tk.Canvas(self.tkRoot, width=270, height=60)
        screen.pack(padx=15, pady=10, fill=tk.X)
        self.digits = []
        for i in range(numDigits):
            self.digits.append(SevenSegDigit(screen, x=10+i*33))
        

tkRoot = tk.Tk()
mk14ui = MK14_UI(tkRoot)
mk14ui.genDigits(8)
mk14ui.genButtons()
n = 0
def update():
    global n
    for i in range(8):
        mk14ui.digits[i].show(n)
    n = (n+1) % 16
    tkRoot.after(1000, update)
tkRoot.after(1000, update)
#root.mainloop()
while True:
    tkRoot.update_idletasks()
    tkRoot.update()
