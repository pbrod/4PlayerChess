#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of the Four-Player Chess project, a four-player chess GUI.
#
# Copyright (C) 2018, GammaDeltaII
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from PyQt5.QtCore import QObject, pyqtSignal, QSettings
from PyQt5.QtGui import QColor
from collections import deque
from datetime import datetime
from re import split
from .board import Board

# Load settings
COM = '4pc'
APP = '4PlayerChess'
SETTINGS = QSettings(COM, APP)


class Algorithm(QObject):
    """The Algorithm is the underlying logic responsible for changing the current state of the board."""
    boardChanged = pyqtSignal(Board)
    gameOver = pyqtSignal(str)
    currentPlayerChanged = pyqtSignal(str)
    fen4Generated = pyqtSignal(str)
    pgn4Generated = pyqtSignal(str)
    moveTextChanged = pyqtSignal(str)
    selectMove = pyqtSignal(tuple)
    removeMoveSelection = pyqtSignal()
    removeHighlight = pyqtSignal(QColor)
    addHighlight = pyqtSignal(int, int, int, int, QColor)
    addArrow = pyqtSignal(int, int, int, int, QColor)  # add arrow for variation
    playerNamesChanged = pyqtSignal(str, str, str, str)
    playerRatingChanged = pyqtSignal(str, str, str, str)
    cannotReadPgn4 = pyqtSignal()

    NoResult, Team1Wins, Team2Wins, Draw = ['*', '1-0', '0-1', '1/2-1/2']  # Results
    NoPlayer, Red, Blue, Yellow, Green = ['?', 'r', 'b', 'y', 'g']  # Players
    PlayerColors = {Red: QColor('#33bf3b43'),
                    Blue: QColor('#334185bf'),
                    Yellow: QColor('#33c09526'),
                    Green: QColor('#334e9161')}

    playerQueue = deque([Red, Blue, Yellow, Green])

    startFen4 = '3yRyNyByKyQyByNyR3/3yPyPyPyPyPyPyPyP3/14/bRbP10gPgR/bNbP10gPgN/bBbP10gPgB/bKbP10gPgQ/' \
                'bQbP10gPgK/bBbP10gPgB/bNbP10gPgN/bRbP10gPgR/14/3rPrPrPrPrPrPrPrP3/3rRrNrBrQrKrBrNrR3 ' \
                'r rKrQbKbQyKyQgKgQ - 0 1'

    # chess.com: [player to move] - [dead 1/0] - [kingside castle 1/0] - [queenside castle 1/0] - [points] - [ply] -
    chesscomStartFen4 = 'R-0,0,0,0-1,1,1,1-1,1,1,1-0,0,0,0-0-3,yR,yN,yB,yK,yQ,yB,yN,yR,3/3,yP,yP,yP,yP,yP,yP,yP,yP,3/' \
                        '14/bR,bP,10,gP,gR/bN,bP,10,gP,gN/bB,bP,10,gP,gB/bK,bP,10,gP,gQ/bQ,bP,10,gP,gK/bB,bP,10,gP,gB/'\
                        'bN,bP,10,gP,gN/bR,bP,10,gP,gR/14/3,rP,rP,rP,rP,rP,rP,rP,rP,3/3,rR,rN,rB,rQ,rK,rB,rN,rR,3'

    def __init__(self):
        super().__init__()
        self.variant = '?'
        self.board = Board(14, 14)
        self.result = self.NoResult
        self.currentPlayer = self.NoPlayer
        self.moveNumber = 0
        self.currentMove = self.Node('root', [], None)
        self.currentMove.fen4 = self.startFen4
        self.redName = self.NoPlayer
        self.blueName = self.NoPlayer
        self.yellowName = self.NoPlayer
        self.greenName = self.NoPlayer
        self.redRating = '?'
        self.blueRating = '?'
        self.yellowRating = '?'
        self.greenRating = '?'
        self.chesscomMoveText = ''
        self.moveText = ''
        self.moveDict = dict()
        self.inverseMoveDict = dict()
        self.index = 0  # Used by getMoveText() method
        self.fenMoveNumber = 1

    @property
    def currentPlayerColor(self):
        return self.PlayerColors.get(self.currentPlayer, QColor('#00000000'))

    class Node:
        """Generic node class. Basic element of a tree."""
        def __init__(self, name, children, parent):
            self.name = name
            self.children = children
            self.parent = parent
            self.fen4 = None
            self.comment = None

        def add(self, node):
            """Adds node to children."""
            self.children.append(node)

        def pop(self):
            """Removes last child from node."""
            self.children.pop()

        def getRoot(self):
            """Backtracks tree and returns root node."""
            if self.parent is None:
                return self
            return self.parent.getRoot()

        def pathFromRoot(self, actions=None):
            """Returns a list of nextMove() actions to reach the current node from the root."""
            if not actions:
                actions = []
            if self.parent is None:
                return actions
            else:
                var = self.parent.children.index(self)
                actions.insert(0, 'nextMove(' + str(var) + ')')
            return self.parent.pathFromRoot(actions)

        def getMoveNumber(self):
            """Returns the move number in the format (ply, variation, move). NOTE: does NOT support subvariations."""
            varNum = [int(a.strip('nextMove()')) for a in self.pathFromRoot()]
            ply, var, move = (0, 0, 0)
            plyCount = True
            i = 0
            while i < len(varNum):
                if varNum[i] != 0:
                    var = varNum[i]
                    plyCount = False
                else:
                    if plyCount:
                        ply += 1
                    else:
                        move += 1
                i += 1
            return str(ply + 1) + '-' + str(var) + '-' + str(move + 1) if var != 0 else str(ply)

    def updatePlayerNames(self, red, blue, yellow, green):
        """Sets player names to names entered in the player name labels."""
        self.redName = red if not (red == 'Player Name' or red == '') else '?'
        self.blueName = blue if not (blue == 'Player Name' or blue == '') else '?'
        self.yellowName = yellow if not (yellow == 'Player Name' or yellow == '') else '?'
        self.greenName = green if not (green == 'Player Name' or green == '') else '?'
        self.getPgn4()  # Update PGN4

    def updatePlayerRating(self, red, blue, yellow, green):
        """Sets player rating to rating entered in the player name labels."""
        self.redRating = red
        self.blueRating = blue
        self.yellowRating = yellow
        self.greenRating = green

    def setResult(self, value):
        """Updates game result, if changed."""
        if self.result == value:
            return
        if self.result == self.NoResult:
            self.result = value
            self.gameOver.emit(self.result)
        else:
            self.result = value
        self.getPgn4()  # Update PGN4

    def setCurrentPlayer(self, value):
        """Updates current player, if changed."""
        if self.currentPlayer == value:
            return
        self.currentPlayer = value
        self.setPlayerQueue(self.currentPlayer)
        self.currentPlayerChanged.emit(self.currentPlayer)

    def setPlayerQueue(self, currentPlayer):
        """Rotates player queue such that the current player is the first in the queue."""
        while self.playerQueue[0] != currentPlayer:
            self.playerQueue.rotate(-1)

    def setBoard(self, board):
        """Updates board, if changed."""
        if self.board == board:
            return
        self.board = board
        self.boardChanged.emit(self.board)

    def setupBoard(self):
        """Initializes board."""
        self.setBoard(Board(14, 14))

    def newGame(self):
        """Initializes board and sets starting position."""
        if SETTINGS.value('chesscom', type='bool'):
            fen4 = self.chesscomStartFen4
        else:
            fen4 = self.startFen4
        self.setBoardState(fen4)
        self.fen4Generated.emit(fen4)

    def getFen4(self, emitSignal=True):
        """Gets FEN4 from current board state."""
        fen4 = self.board.getFen4()
        # Append character for current player
        fen4 += self.currentPlayer + ' '
        fen4 += self.board.castlingAvailability() + ' '
        fen4 += '- '  # En passant target square, n/a
        fen4 += str(self.moveNumber) + ' '  # Number of quarter-moves
        fen4 += str(self.moveNumber // 4 + 1)  # Number of full moves, starting from 1
        if SETTINGS.value('chesscom', type='bool'):
            chesscomPrefix = self.currentPlayer.upper() + '-0,0,0,0' + \
                             self.toChesscomCastling(self.board.castlingAvailability()) + '-0,0,0,0-' + \
                             str(self.moveNumber) + '-'
            fen4 = chesscomPrefix + self.board.getChesscomFen4()
        if emitSignal:
            self.fen4Generated.emit(fen4)
        return fen4

    def toChesscomCastling(self, castling):
        """Converts castling availability string to chess.com compatible format."""
        s = '-'
        s += '1,' if 'rK' in castling else '0,'
        s += '1,' if 'bK' in castling else '0,'
        s += '1,' if 'yK' in castling else '0,'
        s += '1' if 'gK' in castling else '0'
        s += '-'
        s += '1,' if 'rQ' in castling else '0,'
        s += '1,' if 'bQ' in castling else '0,'
        s += '1,' if 'yQ' in castling else '0,'
        s += '1' if 'gQ' in castling else '0'
        return s

    def setCastlingAvailability(self, fen4):
        """Sets castling availability according to FEN4."""
        castling = fen4.split(' ')[2]
        RED, BLUE, YELLOW, GREEN = range(4)
        QUEENSIDE, KINGSIDE = (0, 1)
        self.board.castle[RED][KINGSIDE] = (1 << self.square(10, 0)) if 'rK' in castling else 0
        self.board.castle[RED][QUEENSIDE] = (1 << self.square(3, 0)) if 'rQ' in castling else 0
        self.board.castle[BLUE][KINGSIDE] = (1 << self.square(0, 10)) if 'bK' in castling else 0
        self.board.castle[BLUE][QUEENSIDE] = (1 << self.square(0, 3)) if 'bQ' in castling else 0
        self.board.castle[YELLOW][KINGSIDE] = (1 << self.square(3, 13)) if 'yK' in castling else 0
        self.board.castle[YELLOW][QUEENSIDE] = (1 << self.square(10, 13)) if 'yQ' in castling else 0
        self.board.castle[GREEN][KINGSIDE] = (1 << self.square(13, 3)) if 'gK' in castling else 0
        self.board.castle[GREEN][QUEENSIDE] = (1 << self.square(13, 10)) if 'gQ' in castling else 0

    def setBoardState(self, fen4):
        """Sets board according to FEN4."""
        if not fen4:
            return
        if self.getFen4(False) == fen4:  # Do not emit fen4Generated signal
            return
        self.setupBoard()
        self.board.parseFen4(fen4)
        self.setResult(self.NoResult)
        if SETTINGS.value('chesscom', type='bool'):
            self.setCurrentPlayer(fen4[0].lower())
            self.moveNumber = 0
            self.fenMoveNumber = 1
        else:
            self.setCurrentPlayer(fen4.split(' ')[1])
            self.moveNumber = int(fen4.split(' ')[-2])
            self.fenMoveNumber = int(fen4.split(' ')[-2]) + 1
        self.currentMove = self.Node('root', [], None)
        self.currentMove.fen4 = fen4
        self.chesscomMoveText = ''
        self.moveText = ''
        self.moveDict.clear()
        self.getPgn4()  # Update PGN4

    def toChesscomMove(self, moveString):
        """Converts move string to chess.com move notation."""
        moveString = moveString.split()
        if moveString[0][1] == 'P':
            moveString.pop(0)
            if len(moveString) == 3:
                piece = moveString[1][1]
                if piece != 'P':
                    moveString[1] = 'x' + piece
                else:
                    moveString[1] = 'x'
            else:
                moveString.insert(1, '-')
        elif len(moveString) == 4:
            # Castling move
            shortCastle = ['rK h1 rR k1', 'bK a8 bR a11', 'yK g14 yR d14', 'gK n7 gR n4']
            longCastle = ['rK h1 rR d1', 'bK a8 bR a4', 'yK g14 yR k14', 'gK n7 gR n11']
            if ' '.join(moveString) in shortCastle:
                moveString = 'O-O'
            elif ' '.join(moveString) in longCastle:
                moveString = 'O-O-O'
            else:
                moveString[0] = moveString[0][1]
                piece = moveString[2][1]
                if piece != 'P':
                    moveString[2] = 'x' + piece
                else:
                    moveString[2] = 'x'
        else:
            if moveString != 'O-O' and moveString != 'O-O-O':
                moveString[0] = moveString[0][1]
                moveString.insert(2, '-')
        moveString = ''.join(moveString)
        return moveString

    def fromChesscomMove(self, move, player):
        """Returns fromFile, fromRank, toFile, toRank from chess.com move."""
        if move == 'O-O':
            if player == self.Red:
                fromFile, fromRank, toFile, toRank = (7, 0, 10, 0)
            elif player == self.Blue:
                fromFile, fromRank, toFile, toRank = (0, 7, 0, 10)
            elif player == self.Yellow:
                fromFile, fromRank, toFile, toRank = (6, 13, 3, 13)
            elif player == self.Green:
                fromFile, fromRank, toFile, toRank = (13, 6, 13, 3)
            else:
                fromFile, fromRank, toFile, toRank = [None] * 4
        elif move == 'O-O-O':
            if player == self.Red:
                fromFile, fromRank, toFile, toRank = (7, 0, 3, 0)
            elif player == self.Blue:
                fromFile, fromRank, toFile, toRank = (0, 7, 0, 3)
            elif player == self.Yellow:
                fromFile, fromRank, toFile, toRank = (6, 13, 10, 13)
            elif player == self.Green:
                fromFile, fromRank, toFile, toRank = (13, 6, 13, 10)
            else:
                fromFile, fromRank, toFile, toRank = [None] * 4
        else:
            for c in reversed(move):
                if c.isupper():
                    move = move.replace(c, '')
            move = move.replace('x', '')
            move = move.replace('-', '')
            move = move.replace('+', '')
            move = move.replace('#', '')
            prev = ''
            i = 0
            for char in move:
                if (not char.isdigit()) and prev.isdigit():
                    move = [move[:i], move[i:]]
                    break
                prev = char
                i += 1
            fromFile = ord(move[0][0]) - 97
            fromRank = int(move[0][1:]) - 1
            toFile = ord(move[1][0]) - 97
            toRank = int(move[1][1:]) - 1
        return fromFile, fromRank, toFile, toRank

    def toAlgebraic(self, moveString):
        """Converts move string to algebraic notation."""
        moveString = moveString.split()
        if moveString[0][1] == 'P':
            moveString.pop(0)
            if len(moveString) == 3:
                moveString[1] = 'x'
        elif len(moveString) == 4:
            # Castling move
            shortCastle = ['rK h1 rR k1', 'bK a8 bR a11', 'yK g14 yR d14', 'gK n7 gR n4']
            longCastle = ['rK h1 rR d1', 'bK a8 bR a4', 'yK g14 yR k14', 'gK n7 gR n11']
            if ' '.join(moveString) in shortCastle:
                moveString = 'O-O'
            elif ' '.join(moveString) in longCastle:
                moveString = 'O-O-O'
            else:
                moveString[0] = moveString[0][1]
                moveString[2] = 'x'
        else:
            if moveString != 'O-O' and moveString != 'O-O-O':
                moveString[0] = moveString[0][1]
        moveString = ''.join(moveString)
        return moveString

    def fromAlgebraic(self, move, player):
        """Returns fromFile, fromRank, toFile, toRank from algebraic move."""
        if move == 'O-O':
            if player == self.Red:
                fromFile, fromRank, toFile, toRank = (7, 0, 10, 0)
            elif player == self.Blue:
                fromFile, fromRank, toFile, toRank = (0, 7, 0, 10)
            elif player == self.Yellow:
                fromFile, fromRank, toFile, toRank = (6, 13, 3, 13)
            elif player == self.Green:
                fromFile, fromRank, toFile, toRank = (13, 6, 13, 3)
            else:
                fromFile, fromRank, toFile, toRank = [None] * 4
        elif move == 'O-O-O':
            if player == self.Red:
                fromFile, fromRank, toFile, toRank = (7, 0, 3, 0)
            elif player == self.Blue:
                fromFile, fromRank, toFile, toRank = (0, 7, 0, 3)
            elif player == self.Yellow:
                fromFile, fromRank, toFile, toRank = (6, 13, 10, 13)
            elif player == self.Green:
                fromFile, fromRank, toFile, toRank = (13, 6, 13, 10)
            else:
                fromFile, fromRank, toFile, toRank = [None] * 4
        else:
            for c in reversed(move):  # pab
                if c.isupper():  # pab
                    move = move.replace(c, '')  # pab
            # if move[0].isupper():
            #    move = move[1:]

            move = move.replace('x', '')
            move = move.replace('-', '')  # pab
            move = move.replace('+', '')  # pab
            move = move.replace('#', '')  # pab
            prev = ''
            #i = 0
            for i, char in enumerate(move):
                if (not char.isdigit()) and prev.isdigit():
                    move = [move[:i], move[i:]]
                    break
                prev = char
                # i += 1
            fromFile = ord(move[0][0]) - 97
            fromRank = int(move[0][1:]) - 1
            toFile = ord(move[1][0]) - 97
            toRank = int(move[1][1:]) - 1
        return fromFile, fromRank, toFile, toRank

    def strMove(self, fromFile, fromRank, toFile, toRank):
        """Returns move in string form, separated by spaces, i.e. '<piece> <from> <captured piece> <to>'."""
        piece: str = self.board.getData(fromFile, fromRank)
        captured: str = self.board.getData(toFile, toRank)
        char = (piece + ' ' + chr(97 + fromFile) + str(fromRank + 1) + ' ' + captured * (captured != ' ') + ' ' +
                chr(97 + toFile) + str(toRank + 1))  # chr(97) = 'a'
        return char

    def prevMove(self):
        """Sets board state to previous move."""
        if self.currentMove.name == 'root':
            return
        fromFile, fromRank, toFile, toRank, piece, captured = self._getMove(self.currentMove.name)

        self.board.undoMove(fromFile, fromRank, toFile, toRank, piece, captured)
        self.currentMove = self.currentMove.parent
        self.moveNumber -= 1
        self.playerQueue.rotate(1)
        self.setCurrentPlayer(self.playerQueue[0])
        # Signal View to remove last move highlight
        color = self.currentPlayerColor
        self.removeHighlight.emit(color)
        variations = self.currentMove.children if self.currentMove.children  else [] # and len(nextMove.children)>1
        for nextMove in variations:
            fromFile, fromRank, toFile, toRank = self._getMove(nextMove.name)[:-2]
            self.addArrow.emit(fromFile, fromRank, toFile, toRank, color)
        if not self.currentMove.name == 'root':
            key = self.inverseMoveDict[self.currentMove]
            self.selectMove.emit(key)
        else:
            self.removeMoveSelection.emit()
        self.getFen4()  # Update FEN4
        self.getPgn4()  # Update PGN4

    @staticmethod
    def _getMove(moveString):
        moveString = moveString.split()
        piece = moveString[0]
        fromFile = ord(moveString[1][0]) - 97 # chr(97) = 'a'
        fromRank = int(moveString[1][1:]) - 1
        if len(moveString) == 4:
            captured = moveString[2]
            toFile = ord(moveString[3][0]) - 97
            toRank = int(moveString[3][1:]) - 1
        else:
            captured = ' '
            toFile = ord(moveString[2][0]) - 97
            toRank = int(moveString[2][1:]) - 1
        return fromFile, fromRank, toFile, toRank, piece, captured

    def nextMove(self, var=0):
        """Sets board state to next move. Follows main variation by default (var=0)."""
        if not self.currentMove.children:
            return
        nextMove = self.currentMove.children[var]
        fromFile, fromRank, toFile, toRank = self._getMove(nextMove.name)[:-2]
        self.board.makeMove(fromFile, fromRank, toFile, toRank)
        self.currentMove = nextMove
        self.moveNumber += 1
        # Signal View to add move highlight and remove highlights of next player
        self.addHighlight.emit(fromFile, fromRank, toFile, toRank, self.currentPlayerColor)
        self.playerQueue.rotate(-1)
        self.setCurrentPlayer(self.playerQueue[0])
        color = self.currentPlayerColor
        self.removeHighlight.emit(color)
        variations = nextMove.children if nextMove.children  else [] # and len(nextMove.children)>1
        for nextMove in variations:
            fromFile, fromRank, toFile, toRank = self._getMove(nextMove.name)[:-2]
            self.addArrow.emit(fromFile, fromRank, toFile, toRank, color)
        key = self.inverseMoveDict[self.currentMove]
        self.selectMove.emit(key)
        self.getFen4()  # Update FEN4
        self.getPgn4()  # Update PGN4

    def firstMove(self):
        """Sets board state to first move."""
        while self.currentMove.name != 'root':
            self.prevMove()

    def lastMove(self):
        """Sets board state to last move."""
        self.firstMove()
        while self.currentMove.children:
            self.nextMove()

    def makeMove(self, fromFile, fromRank, toFile, toRank):
        """This method must be implemented to define the proper logic corresponding to the game type (Teams or FFA)."""
        return False

    def getPgn4(self):
        """Generates PGN4 from current game."""
        pgn4 = ''

        # Tags: "?" if data unknown, "-" if not applicable
        pgn4 += '[Variant "' + self.variant + '"]\n'
        pgn4 += '[Site "www.chess.com/4-player-chess"]\n'
        pgn4 += '[Date "' + datetime.utcnow().strftime('%a %b %d %Y %H:%M:%S (UTC)') + '"]\n'
        # pgn4 += '[Event "-"]\n'
        # pgn4 += '[Round "-"]\n'
        pgn4 += '[Red "' + self.redName + '"]\n' if not self.redName == '?' else ''
        pgn4 += '[RedElo "' + self.redRating + '"]\n' if not self.redRating == '?' else ''
        pgn4 += '[Blue "' + self.blueName + '"]\n' if not self.blueName == '?' else ''
        pgn4 += '[BlueElo "' + self.blueRating + '"]\n' if not self.blueRating == '?' else ''
        pgn4 += '[Yellow "' + self.yellowName + '"]\n' if not self.yellowName == '?' else ''
        pgn4 += '[YellowElo "' + self.yellowRating + '"]\n' if not self.yellowRating == '?' else ''
        pgn4 += '[Green "' + self.greenName + '"]\n' if not self.greenName == '?' else ''
        pgn4 += '[GreenElo "' + self.greenRating + '"]\n' if not self.greenRating == '?' else ''
        # pgn4 += '[Result "' + self.result + '"]\n'  # 1-0 (r & y win), 0-1 (b & g win), 1/2-1/2 (draw), * (no result)
        # pgn4 += '[Mode "ICS"]\n'  # ICS = Internet Chess Server, OTB = Over-The-Board
        pgn4 += '[TimeControl "G/1 d15"]\n'  # 1-minute game with 15 seconds delay per move
        pgn4 += '[PlyCount "' + str(self.moveNumber) + '"]\n'  # Total number of quarter-moves
        startFen4 = self.currentMove.getRoot().fen4
        if SETTINGS.value('chesscom', type='bool'):
            if startFen4 != self.chesscomStartFen4:
                pgn4 += '[SetUp "1"]\n'
                pgn4 += '[StartFen4 "' + startFen4 + '"]\n'
        else:
            if startFen4 != self.startFen4:
                pgn4 += '[SetUp "1"]\n'
                pgn4 += '[StartFen4 "' + startFen4 + '"]\n'
        pgn4 += '[CurrentMove "' + self.currentMove.getMoveNumber() + '"]\n'
        pgn4 += '[CurrentPosition "' + self.getFen4() + '"]\n\n'

        # Movetext
        if SETTINGS.value('chesscom', type='bool'):
            pgn4 = pgn4[:-1]  # remove newline
            pgn4 += self.chesscomMoveText
        else:
            pgn4 += self.moveText

            # Append result
            pgn4 += self.result

        self.pgn4Generated.emit(pgn4)

    def updateMoveText(self):
        """Updates movetext and dictionary."""
        self.chesscomMoveText = ''
        self.moveText = ''
        self.moveDict.clear()
        self.index = 0
        self.getMoveText(self.currentMove.getRoot(), self.fenMoveNumber)
        self.inverseMoveDict = {value: key for key, value in self.moveDict.items()}
        self.moveTextChanged.emit(self.moveText)
        if self.currentMove.name != 'root':
            key = self.inverseMoveDict[self.currentMove]
            self.selectMove.emit(key)

    def getMoveText(self, node, move=1, var=0):
        """Traverses move tree to generate movetext and updates move dictionary to keep
        track of the nodes associated with the movetext.
        """
        if node.children:
            main = node.children[0]
            if len(node.children) > 1:
                variations = node.children[1:]
            else:
                variations = None
        else:
            main = None
            variations = None
        # If different FEN4 starting position used, insert move number if needed
        if node.name == 'root' and move != 1 and (move - 1) % 4:
            token = str((move - 1) // 4 + 1) + '.'
            self.chesscomMoveText += token
            self.moveText += token + ' '
            self.moveDict[(self.index, token)] = None
            self.index += 1
            token = '.' * ((move - 1) % 4)
            if token:
                self.moveText += token
                self.moveDict[(self.index, token)] = None
                self.index += 1
            if (move - 1) % 4:
                self.chesscomMoveText += ' '
                self.moveText += ' '
        # Main move has variations
        if main and variations:
            if not (move - 1) % 4:
                token = str(move // 4 + 1) + '.'
                self.chesscomMoveText += '\n' + token + ' '
                self.moveText += token + ' '
                self.moveDict[(self.index, token)] = None
                self.index += 1
            else:
                self.chesscomMoveText += '.. '
            # Add main move to movetext before expanding variations, but do not expand main move yet
            chesscomToken = self.toChesscomMove(main.name)
            self.chesscomMoveText += chesscomToken + ' '
            token = self.toAlgebraic(main.name)
            self.moveText += token + ' '
            self.moveDict[(self.index, token)] = main
            self.index += 1
            if main.comment:
                self.chesscomMoveText += '{ ' + main.comment + ' } '
                self.moveText += '{ ' + main.comment + ' } '
            # Expand variations
            for variation in variations:
                if self.moveText[-2] == ')':
                    self.index += 1
                token = '('
                self.chesscomMoveText += token + ' '
                self.moveText += token + ' '
                self.moveDict[(self.index, token)] = None
                self.index += 1
                token = str(move // 4 + 1)
                self.chesscomMoveText += token
                self.moveText += token + ' '
                self.moveDict[(self.index, token)] = None
                self.index += 1
                token = '.' * ((move - 1) % 4)
                if token:
                    self.moveText += token
                    self.moveDict[(self.index, token)] = None
                    self.index += 1
                if (move - 1) % 4:
                    self.chesscomMoveText += '.. '
                    self.moveText += ' '
                else:
                    self.chesscomMoveText += '. '
                chesscomToken = self.toChesscomMove(variation.name)
                self.chesscomMoveText += chesscomToken + ' '
                token = self.toAlgebraic(variation.name)
                self.moveText += token + ' '
                self.moveDict[(self.index, token)] = variation
                self.index += 1
                if variation.comment:
                    self.chesscomMoveText += '{ ' + variation.comment + ' } '
                    self.moveText += '{ ' + variation.comment + ' } '
                self.getMoveText(variation, move + 1, var + 1)
            # Expand main move
            self.index += 1
            self.getMoveText(main, move + 1, var)
        # Main move has no variations
        elif main and not variations:
            if not (move - 1) % 4:
                token = str(move // 4 + 1) + '.'
                self.chesscomMoveText += '\n' + token + ' '
                self.moveText += token + ' '
                self.moveDict[(self.index, token)] = None
                self.index += 1
            else:
                self.chesscomMoveText += '.. '
            chesscomToken = self.toChesscomMove(main.name)
            self.chesscomMoveText += chesscomToken + ' '
            token = self.toAlgebraic(main.name)
            self.moveText += token + ' '
            self.moveDict[(self.index, token)] = main
            self.index += 1
            if main.comment:
                self.chesscomMoveText += '{ ' + main.comment + ' } '
                self.moveText += '{ ' + main.comment + ' } '
            self.getMoveText(main, move + 1, var)
        # Node is leaf node (i.e. end of variation or main line)
        else:
            if var != 0:
                token = ')'
                self.chesscomMoveText += token + ' '
                self.moveText += token + ' '
                self.moveDict[(self.index, token)] = None

    @staticmethod
    def split_(movetext):
        """Splits movetext into tokens."""
        # regex: one or more spaces followed by { or preceded by }
        x = split('\s+(?={)|(?<=})\s+', movetext)
        movetext = []
        for y in x:
            if y:
                if y[0] != '{':
                    for z in y.split():
                        movetext.append(z)
                else:
                    movetext.append(y)
        return movetext

    def parseChesscomPgn4(self, pgn4):
        """Parses chess.com PGN4 and sets game state accordingly."""
        # startPosition = None  # TODO: Delete? it is unused
        currentMove = None
        lines = pgn4.split('\n')
        movetext = ''
        attributes = {'Red': 'redName',
                      'RedElo': 'redRating',
                      'Blue': 'blueName',
                      'BlueElo': 'blueRating',
                      'Yellow': 'yellowName',
                      'YellowElo': 'yellowRating',
                      'Green': 'greenName',
                      'GreenElo': 'greenRating',
                      'Result': 'result'
                      }
        for line in lines:
            line = line.strip()  # pab
            if line == '':
                continue
            elif line[0] == '[' and line[-1] == ']':
                #==================================================================================
                # Tags section
                #==================================================================================
                tag = line.strip('[]').split('"')[:-1]
                tag[0] = tag[0].strip()
                if tag[0] == 'Variant' and tag[1] == 'FFA':
                    self.cannotReadPgn4.emit()
                    return False
                name = attributes.get(tag[0])
                if name is not None:
                    setattr(self, name, tag[1])
                elif tag[0] == 'CurrentMove':
                    currentMove = tag[1]
                # else: # Irrelevant tags
                continue
            else:
                if not currentMove:
                    self.cannotReadPgn4.emit()
                    return False
                movetext += line + ' '

            #======================================================================================
            # Movetext section
            #======================================================================================
            # Generate game from movetext
            self.newGame()
            tokens = self.split_(movetext)
            for token in tokens:
                if token[0] == '(' and len(token) > 1:
                    index = tokens.index(token)
                    tokens.insert(index + 1, token[1:])
                    tokens[index] = token[0]
            roots = []
            prev = None
            # i = 0
            for i, token in enumerate(tokens):
                try:
                    next_ = tokens[i + 1]
                except IndexError:
                    next_ = None
                if (token[0].isdigit() and token[-1] == '.') or token in '..RT#':
                    pass
                elif token[0] == '{':
                    # Comment
                    self.currentMove.comment = token[1:-1].strip()
                elif token == '(':
                    # Next move is variation
                    if not prev == ')':
                        self.prevMove()
                    roots.append(self.currentMove)
                elif token == ')':
                    # End of variation
                    root = roots.pop()
                    while self.currentMove.name != root.name:
                        self.prevMove()
                    if next_ != '(':
                        # Continue with previous line
                        self.nextMove()
                else:
                    # try: # TODO: Crashes frequently here! (typically token="*")
                    fromFile, fromRank, toFile, toRank = self.fromChesscomMove(token,
                                                                               self.currentPlayer)
                    self.makeMove(fromFile, fromRank, toFile, toRank)
                    # except Exception as error:
                    #    print(error)

                prev = token
                # i += 1
        # Set game position to CurrentMove ("ply-variation-move")
        self.firstMove()
        currentMove = [int(c) for c in currentMove.split('-')]
        if len(currentMove) == 1:
            ply = currentMove[0]
            for _ in range(ply):
                self.nextMove()
        else:
            ply, variation, move = currentMove
            for _ in range(ply - 1):
                self.nextMove()
            self.nextMove(variation)
            for _ in range(move - 1):
                self.nextMove()
        # Emit signal to update player names and rating
        self.playerNamesChanged.emit(self.redName, self.blueName, self.yellowName, self.greenName)
        self.playerRatingChanged.emit(self.redRating, self.blueRating, self.yellowRating, self.greenRating)
        return True

    def parsePgn4(self, pgn4):
        """Parses PGN4 and sets game state accordingly.

        References
        ----------
        https://en.wikibooks.org/wiki/Four-Player_Chess/Notation
        https://en.wikipedia.org/wiki/Portable_Game_Notation
        https://ia802908.us.archive.org/26/items/pgn-standard-1994-03-12/PGN_standard_1994-03-12.txt

        Algebraic notation
        ------------------
        For four-player chess the same algebraic notation as for regular chess can be used:

        K = king
        Q = queen
        R = rook
        B = bishop
        N = knight
        No letter is used for pawn moves.

        When the move is a capture, an x is inserted between the origin and destination square.
        If two pieces of the same type can move to the same square, the file or rank of origin
        (or both, if necessary) are added after the piece's letter.
        Pawn promotion is indicated by appending =Q to the move (or, in case of underpromotion, =N, =B or =R).
        Kingside castling (short castle) is notated as O-O.
        Queenside castling  (long castle) is notated as O-O-O.
        Check is indicated by appending + to the move and
        in case of double and triple check ++ and +++, respectively.
        Checkmate is indicated by appending # to the move.
        Piece manoeuvres are notated as the piece letter followed by the origin square,
        any intermediate squares and the destination square, separated by a hyphen,
        e.g. Qg1-k5-g9.
        In case of manoeuvres involving captures, the moves are written in full,
        separated by hyphens, e.g. Nk12-Nxm11-Nxn9.
        Diagonals are notated as start and end square, separated by a hyphen.
        Diagonals are always considered from left to right, hence the start square is the
        leftmost square, i.e. start and end are in alphabetical order in terms of files.
        For example, "e14-n5 diagonal" and not "n5-e14 diagonal".
        Other common annotations include:

        ! = good move
        !! = excellent move
        ? = bad move
        ?? = blunder
        !? = potentially interesting move
        ?! = dubious move

        Long algebraic notation
        -----------------------
        Alternatively, long algebraic notation can be used for clarity.
        In long algebraic notation both the origin and destination square are indicated,
        separated by a hyphen, e.g. Qn8-m9. When the move is a capture, the hyphen is
        replaced by an x and the letter of the captured piece is also included, e.g. Qg1xQn8+.


        The movetext describes the actual moves of the game. This includes move number
        indicators (numbers followed by either one or three periods; one if the next move
        is White's move, three if the next move is Black's move) and movetext in Standard
        Algebraic Notation (SAN).

        For most moves the SAN consists of the letter abbreviation for the piece, an x if
        there is a capture, and the two-character algebraic name of the final square the
        piece moved to. The letter abbreviations are K (king), Q (queen), R (rook),
        B (bishop), and N (knight). The pawn is given an empty abbreviation in SAN movetext,
        but in other contexts the abbreviation P is used. The algebraic name of any square
        is as per usual algebraic chess notation; from white's perspective,
        the leftmost square closest to white is a1, the rightmost square closest to the
        white is h1, and the rightmost (from white's perspective) square closest to black
        side is h8.

        In a few cases a more detailed representation is needed to resolve ambiguity;
        if so, the piece's file letter, numerical rank, or the exact square is inserted
        after the moving piece's name (in that order of preference). Thus, Nge2 specifies
        that the knight originally on the g-file moves to e2.

        SAN kingside castling is indicated by the sequence O-O;
        queenside castling is indicated by the sequence O-O-O (note that these are capital Os,
        not zeroes, contrary to the FIDE standard for notation).
        [3] Pawn promotions are notated by appending = to the destination square,
        followed by the piece the pawn is promoted to. For example: e8=Q. If the move is a
        checking move, + is also appended; if the move is a checkmating move, # is appended
        instead. For example: e8=Q#.

        An annotator who wishes to suggest alternative moves to those actually played in the
        game may insert variations enclosed in parentheses. They may also comment on the game
        by inserting Numeric Annotation Glyphs (NAGs) into the movetext. Each NAG reflects a
        subjective impression of the move preceding the NAG or of the resultant position.

        If the game result is anything other than *, the result is repeated at the end of
        the movetext.
        """

        currentPosition = None
        lines = pgn4.split('\n')
        attributes = {'Red': 'redName',

                      'Blue': 'blueName',

                      'Yellow': 'yellowName',

                      'Green': 'greenName',

                      'Result': 'result'
                      }
        for line in lines:
            line = line.strip()  # pab
            if line == '':
                continue
            if line[0] == '[' and line[-1] == ']':
                # tag pair section
                tag = line.strip('[]').split('"')[:-1]
                tag[0] = tag[0].strip()
                if tag[0] == 'Variant' and tag[1] == 'FFA':
                    self.cannotReadPgn4.emit()
                    return False
                name = attributes.get(tag[0])
                if name is not None:
                    setattr(self, name, tag[1])
                elif tag[0] == 'CurrentPosition':
                    currentPosition = tag[1]
                # else: # Irrelevant tags
                continue
            
            if not currentPosition:
                self.cannotReadPgn4.emit()
                return False
            # movetext section.
            # Generate game from movetext
            self.newGame()
            line = line.replace(' *', '')
            line = line.replace(' 1-0', '')
            line = line.replace(' 0-1', '')
            line = line.replace(' 1/2-1/2', '')
            if line == '*':
                # No movetext to process
                break
            roots = []
            tokens = self.split_(line)
            prev = None
            i = 0
            for token in tokens:
                try:
                    next_ = tokens[i + 1]
                except IndexError:
                    next_ = None
                if token[0].isdigit() or token[0] == '.':
                    pass
                elif token[0] == '{':
                    # Comment
                    self.currentMove.comment = token[1:-1].strip()
                elif token == '(':
                    # Next move is variation
                    if not prev == ')':
                        self.prevMove()
                    roots.append(self.currentMove)
                elif token == ')':
                    # End of variation
                    root = roots.pop()
                    while self.currentMove.name != root.name:
                        self.prevMove()
                    if next_ != '(':
                        # Continue with previous line
                        self.nextMove()
                else:
                    fromFile, fromRank, toFile, toRank = self.fromAlgebraic(token, self.currentPlayer)
                    self.makeMove(fromFile, fromRank, toFile, toRank)
                prev = token
                i += 1
        # Set game position to FEN4
        self.firstMove()
        node = None
        for node in self.traverse(self.currentMove, self.currentMove.children):
            if node.fen4 == currentPosition:
                break
        if node:
            actions = node.pathFromRoot()
            for action in actions:
                exec('self.' + action)
        # Emit signal to update player names
        self.playerNamesChanged.emit(self.redName, self.blueName, self.yellowName, self.greenName)
        return True

    def traverse(self, tree, children):
        """Traverses nodes of tree in breadth-first order."""
        yield tree
        last = tree
        for node in self.traverse(tree, children):
            for child in node.children:
                yield child
                last = child
            if last == node:
                return


class Teams(Algorithm):
    """A subclass of Algorithm for the 4-player chess Teams variant."""
    def __init__(self):
        super().__init__()
        self.variant = 'Teams'

    def makeMove(self, fromFile, fromRank, toFile, toRank):
        """Moves piece from square (fromFile, fromRank) to square (toFile, toRank), if the move is valid."""
        if self.currentPlayer == self.NoPlayer:
            return False
        # Check if square contains piece of current player. (A player may only move his own pieces.)
        fromData = self.board.getData(fromFile, fromRank)
        if self.currentPlayer == self.Red and fromData[0] != 'r':
            return False
        if self.currentPlayer == self.Blue and fromData[0] != 'b':
            return False
        if self.currentPlayer == self.Yellow and fromData[0] != 'y':
            return False
        if self.currentPlayer == self.Green and fromData[0] != 'g':
            return False

        # TODO check if move is truly legal (checks)
        color = ['r', 'b', 'y', 'g'].index(fromData[0])
        piece = ['P', 'N', 'B', 'R', 'Q', 'K'].index(fromData[1]) + 4
        origin = self.board.square(fromFile, fromRank)
        target = self.board.square(toFile, toRank)
        if not (1 << target) & self.board.legalMoves(piece, origin, color):
            return False

        # Check if move already exists
        moveString = self.strMove(fromFile, fromRank, toFile, toRank)
        if not (self.currentMove.children and (moveString in (child.name for child in self.currentMove.children))):
            # Make move child of current move and update current move (i.e. previous move is parent of current move)
            move = self.Node(moveString, [], self.currentMove)
            self.currentMove.add(move)
            self.currentMove = move
            # Update movetext and move dictionary and select current move in move list
            self.updateMoveText()
        else:
            # Move already exists. Update current move, but do not change the move tree
            for child in self.currentMove.children:
                if child.name == moveString:
                    self.currentMove = child
                    self.updateMoveText()  # Make current move selected in move list

        # Make the move
        self.board.makeMove(fromFile, fromRank, toFile, toRank)

        # Increment move number
        self.moveNumber += 1

        # Rotate player queue and get next player from the queue (first element)
        self.playerQueue.rotate(-1)
        self.setCurrentPlayer(self.playerQueue[0])

        # Update FEN4 and PGN4
        fen4 = self.getFen4()
        self.getPgn4()

        # Store FEN4 in current node
        self.currentMove.fen4 = fen4

        return True


class FFA(Algorithm):
    """A subclass of Algorithm for the 4-player chess Free-For-All (FFA) variant."""
    # TODO implement FFA class
    def __init__(self):
        super().__init__()
        self.variant = 'Free-For-All'
