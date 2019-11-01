from PyQt5 import QtWidgets, QtCore, QtGui
import sqlite3

from StatisticsWindow import StatisticsWindow
from BoardWidget import BoardWidget
from ChoosePlayersDialog import ChoosePlayersDialog

from config import *

import uiFiles.MainWindowUi as MainWindowUi


class MainWindow(QtWidgets.QMainWindow, MainWindowUi.Ui_mainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setupUi(self)
        self.initUi()

    def initUi(self):
        self.actionNewGame.triggered.connect(self.newGame)
        self.actionSeeStatistics.triggered.connect(self.openStatisticsWindow)

        self.board = BoardWidget(self)
        self.board.move(5, 30)
        self.board.gameEnded.connect(self.gameEnded)
        self.board.moveMade.connect(self.inGameUpdate)

        self.firstPlayerSurrenderBtn.clicked.connect(self.surrender)
        self.secondPlayerSurrenderBtn.clicked.connect(self.surrender)

    def newGame(self):
        gameStarted = self.board.isGameStarted()

        if gameStarted is True:
            force = QtWidgets.QMessageBox\
                    .question(self,
                              "",
                              """Do you really want to start new game?
This game is not ended.""",
                              QtWidgets.QMessageBox.Yes |
                              QtWidgets.QMessageBox.No)

            if force != QtWidgets.QMessageBox.Yes:
                return

        self.choosePlayersDialog = ChoosePlayersDialog(self)
        playersChoosen = self.choosePlayersDialog.exec()

        if playersChoosen:
            self.firstPlayer = self.choosePlayersDialog.getFirstPlayerData()
            self.secondPlayer = self.choosePlayersDialog.getSecondPlayerData()
            self.choosePlayersDialog.close()
        else:
            self.choosePlayersDialog.close()
            return

        self.firstPlayerNickname.setText(self.firstPlayer[1])
        self.secondPlayerNickname.setText(self.secondPlayer[1])

        self.movesList.clear()

        self.actionSeeStatistics.setEnabled(False)

        self.board.startGame(force=True)

    def inGameUpdate(self, move):
        self.firstPlayerSurrenderBtn.setEnabled(True)
        self.secondPlayerSurrenderBtn.setEnabled(True)

        self.movesList.addItem(move.uci())

    def gameEnded(self, result):
        self.movesList.addItem(result)

        self.con = sqlite3.connect(DB_PATH)

        cur = self.con.cursor()

        firstPlayerStats = list(cur.execute("""SELECT games_played, games_won,
games_draw, games_lost
FROM Players
WHERE id = ?""", (self.firstPlayer[0], )).fetchone())

        secondPlayerStats = list(cur.execute("""SELECT games_played, games_won,
games_draw, games_lost
FROM Players
WHERE id = ?""", (self.secondPlayer[0], )).fetchone())

        firstPlayerStats[0] += 1
        secondPlayerStats[0] += 1

        if result == "1-0":
            firstPlayerStats[1] += 1
            secondPlayerStats[3] += 1
        elif result == "1/2-1/2":
            firstPlayerStats[2] += 1
            secondPlayerStats[2] += 1
        else:
            firstPlayerStats[3] += 1
            secondPlayerStats[1] += 1

        cur.execute("""UPDATE Players
SET games_played = ?,
    games_won = ?,
    games_draw = ?,
    games_lost = ?
WHERE id = ?""", (*firstPlayerStats, self.firstPlayer[0]))

        cur.execute("""UPDATE Players
SET games_played = ?,
    games_won = ?,
    games_draw = ?,
    games_lost = ?
WHERE id = ?""", (*secondPlayerStats, self.secondPlayer[0]))

        self.con.commit()
        self.con.close()

        self.firstPlayerSurrenderBtn.setEnabled(False)
        self.secondPlayerSurrenderBtn.setEnabled(False)

        self.actionSeeStatistics.setEnabled(True)

    def surrender(self):
        if self.sender() is self.firstPlayerSurrenderBtn:
            self.board.surrender(WHITE_SIDE)
        else:
            self.board.surrender(BLACK_SIDE)

    def openStatisticsWindow(self):
        self.statisticsWindow = StatisticsWindow(self)
        self.statisticsWindow.show()
