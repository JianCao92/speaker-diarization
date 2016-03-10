#!/usr/bin/python2
import argparse
import sys
import mplayer as mp
import curses


def updatemarks(mwin, marks, remove=False, add=False, edit=False, pgUp=False,
                pgDwn=False):
    maxlines = mwin.getmaxyx()[0]
    # Moving in half-pages is better to track where we were
    if pgUp:
        updatemarks.count -= maxlines / 2
        if updatemarks.count < 1:
            updatemarks.count = 1
    elif pgDwn:
        updatemarks.count += maxlines / 2
        if updatemarks.count >= len(marks):
            updatemarks.count = len(marks)
    mwin.vline(0, 0, 0, maxlines)
    mwin.addstr(0, 2, 'Marks:\n')
    if remove:
        curses.echo()
        mwin.addstr(0, 16, 'Mark to remove? ')
        m = mwin.getstr()
        try:
            mwin.addstr(0, 16, 'Removed mark at: ' +
                        str(marks.pop(int(m) - 1)) + '\n')
        except (ValueError, IndexError):
            mwin.addstr(0, 16, 'Invalid mark index: ' + m + '\n')
        curses.noecho()
    if add:
        curses.echo()
        mwin.addstr(0, 16, 'Add mark at? ')
        val = mwin.getstr()
        try:
            mwin.addstr(0, 16, 'Added mark at: ' + val + '\n')
            marks.append(float(val))
        except (ValueError, IndexError):
            mwin.addstr(0, 16, 'Invalid mark value: ' + val + '\n')
        curses.noecho()
    if edit:
        curses.echo()
        mwin.addstr(0, 16, 'Mark to manually edit? ')
        m = mwin.getstr()
        try:
            mwin.addstr(0, 16, 'Insert mark ' + m + ' new value: ')
            val = mwin.getstr()
            mwin.addstr(0, 16, 'Updated mark ' + m + '\n')
            marks[int(m) - 1] = float(val)
        except (ValueError, IndexError):
            mwin.addstr(0, 16, 'Invalid mark index: ' + m + '\n')
        curses.noecho()
    marks.sort()
    lincount = 1
    for m in marks[updatemarks.count - 1:]:
        mwin.addstr(mwin.getyx()[0], 2, str(updatemarks.count - 1 + lincount)
                    + ': ' + str(m) + '\n')
        lincount += 1
        if lincount >= maxlines - 1:
            break
    # Clean lines in case we delete the last ones
    for l in xrange(lincount + 1, maxlines):
        mwin.addstr(mwin.getyx()[0], 2, '\n')

    mwin.refresh()


def writebuf(marks, outf):
    outf.write('#' + args.infile + '\n')
    for l in marks:
        outf.write(str(l) + '\n')


def main(infile, marks, outf):
    # Curses initialization
    stdscr = curses.initscr()
    curses.noecho()
    curses.cbreak()
    curses.curs_set(False)
    # Main screen
    maxlines = stdscr.getmaxyx()[0]
    scr = stdscr.subwin(maxlines, 32, 0, 0)
    scr.nodelay(True)
    scr.keypad(True)
    # Prepare marks window
    mwin = stdscr.subwin(0, 33)
    # mwin.scrollok(True)
    # mplayer initialization
    p = mp.Player()
    p.loadfile(infile)
    # Start paused
    p.pause()
    p.time_pos = 0.0
    scr.addstr('Total time: ')
    scr.addstr(str(p.length))
    scr.addstr(' seconds\n')
    scr.addstr(6, 0, 'Pause: ' + str(p.paused) + '\n')
    scr.addstr(8, 0, 'Default keys:\n')
    scr.addstr('Quit: <esc> or q\n')
    scr.addstr('Pause: p\n')
    scr.addstr('Mark position: <space>\n')
    scr.addstr('Manually edit mark: e\n')
    scr.addstr('Add manual mark: a\n')
    scr.addstr('Remove mark: r\n')
    scr.addstr('Faster speed: <Key-Up>\n')
    scr.addstr('Slower speed: <Key-Down>\n')
    scr.addstr('Rewind: <Key-Left>\n')
    scr.addstr('Fast Forward: <Key-Right>\n')
    scr.addstr('Scroll down marks: <Key-pgDwn>\n')
    scr.addstr('Scroll up marks: <Key-pgUp>\n')
    pausedhere = False
    moveFirstTime = True
    movePos = 0.0
    updatemarks.count = 1  # Start showing from the first mark
    updatemarks(mwin, marks)
    # Main loop
    while True:
        scr.addstr(1, 0, 'Time: ')
        if moveFirstTime:
            movePos = p.time_pos
        scr.addstr(str(movePos))
        scr.addstr(' seconds\n')
        scr.refresh()
        # updatemarks(mwin, marks, maxlines)
        c = scr.getch()
        if c == ord('q') or c == 27:
            break
        elif c == ord(' '):  # Space pressed
            if not p.paused:
                p.pause()  # Make sure both screen and file has the same time
                pausedhere = True
            scr.addstr(2, 0, 'Mark at: ' + str(p.time_pos) + ' seconds\n')
            marks.append(p.time_pos)
            updatemarks(mwin, marks)
            if pausedhere:
                pausedhere = False
                p.pause()
        elif c == ord('e'):
            if not p.paused:
                p.pause()
                pausedhere = True
            if len(marks) > 0:
                updatemarks(mwin, marks, edit=True)
            else:
                scr.addstr(5, 0, 'No mark to edit\n')
            if pausedhere:
                pausedhere = False
                p.pause()
        elif c == ord('a'):
            if not p.paused:
                p.pause()
                pausedhere = True
            updatemarks(mwin, marks, add=True)
            if pausedhere:
                pausedhere = False
                p.pause()
        elif c == ord('r'):
            if not p.paused:
                p.pause()
                pausedhere = True
            if len(marks) > 0:
                updatemarks(mwin, marks, remove=True)
            else:
                scr.addstr(5, 0, 'No mark to remove\n')
            if pausedhere:
                pausedhere = False
                p.pause()
        elif c == ord('p'):
            if not moveFirstTime:
                moveFirstTime = True
                p.time_pos = movePos
            p.pause()
            scr.addstr(6, 0, 'Pause: ' + str(p.paused) + '\n')
        elif c == curses.KEY_UP:
            if not p.paused:
                p.pause()
                pausedhere = True
            p.speed_incr(0.05)
            scr.addstr(3, 0, 'Speed set at: x' + str(p.speed) + '\n')
            if pausedhere:
                pausedhere = False
                p.pause()
        elif c == curses.KEY_DOWN:
            if not p.paused:
                p.pause()
                pausedhere = True
            p.speed_incr(-0.05)
            scr.addstr(3, 0, 'Speed set at: x' + str(p.speed) + '\n')
            if pausedhere:
                pausedhere = False
                p.pause()
        elif c == curses.KEY_LEFT:
            if not p.paused:
                p.pause()
                pausedhere = True
            if moveFirstTime:
                movePos = p.time_pos
                moveFirstTime = False
            movePos -= TIME_STEP
            scr.addstr(4, 0, 'Back to ' + str(movePos) + ' seconds\n')
            if pausedhere:
                pausedhere = False
                moveFirstTime = True
                p.time_pos = movePos
                p.pause()
        elif c == curses.KEY_RIGHT:
            if not p.paused:
                p.pause()
                pausedhere = True
            if moveFirstTime:
                movePos = p.time_pos
                moveFirstTime = False
            movePos += TIME_STEP
            scr.addstr(4, 0, 'Forward to ' + str(movePos) + ' seconds\n')
            if pausedhere:
                pausedhere = False
                moveFirstTime = True
                p.time_pos = movePos
                p.pause()
        elif c == curses.KEY_PPAGE:
            updatemarks(mwin, marks, pgUp=True)
        elif c == curses.KEY_NPAGE:
            updatemarks(mwin, marks, pgDwn=True)

    # Write the output
    if outf is not None:
        writebuf(marks, outf)

    # Reset terminal to normal operation before quitting
    curses.echo()
    curses.nocbreak()
    curses.curs_set(True)
    scr.keypad(False)
    stdscr.nodelay(False)
    curses.endwin()
    sys.exit()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Helps to mark positions in a\
                                                  media file.')
    parser.add_argument('infile', type=str,
                        help='Specifies the input file')
    parser.add_argument('-o', dest='outfile', type=str, default=sys.stdout,
                        help='Specifies an output file.')
    parser.add_argument('-i', dest='mfile', type=str, default=None,
                        help='Specifies an existing marks input file.')
    parser.add_argument('-ts', dest='timestep', type=float, default=1.0,
                        help='Specifies the timestep for jumping forwards or\
                              backwards, default 1.0 seconds.')
    args = parser.parse_args()

    # Process arguments
    print 'Reading file from:', args.infile
    marks = []
    if args.mfile is not None:
        print 'Reading existing marks file from:', args.mfile
        with open(args.mfile, 'r') as mfile:
            mfile.readline() # Skip filename
            for m in mfile:
                marks.append(float(m))

    if args.outfile != sys.stdout:
        outfile = args.outfile
        print 'Writing output to:', args.outfile
    else:
        outfile = sys.stdout
        print 'Writing output to: stdout'

    TIME_STEP = args.timestep

    # End of argument processing

    # Do the real work
    if outfile != sys.stdout:
        with open(outfile, 'w') as outf:
            main(args.infile, marks, outf)
    else:
        main(args.infile, marks, None)
