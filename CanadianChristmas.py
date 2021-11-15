import os, sys, random, smtplib
from PySide2.QtCore import *
from PySide2.QtWidgets import *
from PySide2.QtUiTools import *
from PySide2.QtGui import *

# add new user
def addUser():
	ui.users.insertRow(ui.users.rowCount())
	userSelectionChanged()

# remove selected user
def removeUser():
	rowPosition = ui.users.currentRow()
	if rowPosition>=0:
		ui.users.removeRow(rowPosition)
		userSelectionChanged()

# remove all users
def removeAllUsers():
	ui.users.setRowCount(0)
	userSelectionChanged()

# update table control on users' changes
def userSelectionChanged():
	ui.removeUser.setEnabled(ui.users.currentRow()>=0)
	ui.removeAllUsers.setEnabled(ui.users.rowCount()>0)

# confirmation box
def Confirm(sTitle, sText):
	dialog = QMessageBox()
	dialog.setIcon(QMessageBox.Warning)
	dialog.setWindowTitle(sTitle)
	dialog.setText(sText)
	dialog.setStandardButtons(QMessageBox.Cancel | QMessageBox.Ok)
	dialog.setDefaultButton(QMessageBox.Cancel)
	ret = dialog.exec_()
	if ret == dialog.Ok:
		return True
	return False

# information box
def InformationBox(sTitle, sText):
	dialog = QMessageBox()
	dialog.setIcon(QMessageBox.Warning)
	dialog.setWindowTitle(sTitle)
	dialog.setText(sText)
	dialog.setStandardButtons(QMessageBox.Ok)
	dialog.setDefaultButton(QMessageBox.Ok)
	dialog.exec_()

# Check excludes
def checkExcludes(l):
	rowCount = ui.users.rowCount()
	for index in l:
		excludes = ui.users.item(index, 2)
		if excludes:
			nextRow = index+1
			if nextRow>=rowCount:
				nextRow = 0
			currentText = ui.users.item(index, 0).text()
			selectedText = ui.users.item(nextRow, 0).text()
			excludesText = excludes.text()
			if excludesText.find(selectedText) >= 0:
				print(currentText+'> '+'selected:'+selectedText+' excludes:'+excludesText)
				return False
	return True

class userGroup:
	def __init__(self, name):
		self.name = str(name)
		self.lUsers = []
	def checkName(self, name):
		return self.name == name
	def name(self):
		return self.name
	def users(self):
		return self.lUsers
	def push(self, index):
		self.lUsers.append(index)
	def pop(self):
		if len(self.lUsers)>0:
			return self.lUsers.pop()
		else:
			return None
	def remove(index):
		self.lUsers.remove(index)
	def shuffle(self):
		random.shuffle(self.lUsers)

def getGroupLength(group):
	return len(group.lUsers)

def shuffle():
	# sort user by group
	lGroups = []
	for rowIndex in range(ui.users.rowCount()):
		groupName = ''
		group = ui.users.item(rowIndex, 2)
		if group:
			groupName = group.text()
		groupFound = False
		for group in lGroups:
			if group.checkName(groupName):
				group.push(rowIndex)
				groupFound = True
		if not groupFound:
			newGroup = userGroup(groupName)
			newGroup.push(rowIndex)
			lGroups.append(newGroup)
	# shuffle each group
	for group in lGroups:
		group.shuffle()
	# shuffle groups then sort them by size (biggest first)
	random.shuffle(lGroups)
	lGroups.sort(key=getGroupLength, reverse=True)
	# compute final distribution
	lShuffled = []
	for group in lGroups:
		for i in range(len(group.lUsers)):
			pivot = i*2
			if pivot<len(lShuffled):
				lShuffled.insert(pivot, group.lUsers[i])
			else:
				lShuffled.append(group.lUsers[i])
	# done
	return lShuffled

# shuffle users & send emails
def publish():
	rowCount = ui.users.rowCount()
	if rowCount > 2:
		if not Confirm("Proceed?", "Proceed with publish?"):
			return
		# shuffle users
		lShuffledUserIndexes = shuffle()
		# open smtp server
		smtpObj = smtplib.SMTP(ui.smtpServer.text(), ui.smtpPort.text())
		type(smtpObj)
		try: 
			smtpObj.ehlo()
		except smtplib.SMTPException as e: 
			InformationBox("Failed to send emails", e)
			return
		try: 
			smtpObj.starttls()
		except smtplib.SMTPException as e: 
			InformationBox("Failed to send emails", e)
			return
		try: 
			smtpObj.login(' '+ui.smtpLogin.text()+' ', ' '+ui.smtpPassword.text()+' ')
		except smtplib.SMTPException as e: 
			InformationBox("Failed to send emails", e)
			return
		# send emails
		report = str()
		senderAddress = ui.senderAddress.text()
		for i in range(len(lShuffledUserIndexes)):
			address = ui.users.item(lShuffledUserIndexes[i], 1).text()
			name = ui.users.item(lShuffledUserIndexes[i], 0).text()
			next = i+1
			if next>=len(lShuffledUserIndexes):
				next = 0
			receiverName = ui.users.item(lShuffledUserIndexes[next], 0).text()
			text = 'Subject: Canadian christmas\n'+name+', you were picked to find a gift for '+receiverName+'!\nCanadian christmas date: '+ui.date.text()+'\nMax budget: '+ui.maxBudget.text()+'\n'
			report = report+text
			try: 
				smtpObj.sendmail(' '+senderAddress+' ', ' '+toAddress+' ', text)
			except smtplib.SMTPException as e: 
				InformationBox("Failed to send emails", e)
				return
		# close smtp server
		smtpObj.quit()
		# dump report
		f = open(os.path.join(os.getcwd(), 'report.txt'), 'w')
		f.write(report)
		f.close()
		# done
		InformationBox("Done", "Publish done.")
	else:
		InformationBox("Error", "Please register at least 3 users...")

# settings serializers
def readTextSetting(item, settingId):
	setting = settings.value(settingId)
	if setting:
		item.setText(setting)

def writeTextSetting(item, settingId):
	settings.setValue(settingId, item.text())

def readTableSetting(item, settingId):
	rowCount = settings.value(settingId+'.rowCount')
	if rowCount:
		item.setRowCount(rowCount)
		for rowIndex in range(rowCount):
			for columnIndex in range(item.columnCount()):
				itemValue = settings.value(settingId+'['+str(rowIndex)+','+str(columnIndex)+']')
				if itemValue:
					item.setItem(rowIndex, columnIndex, QTableWidgetItem(itemValue))

def writeTableSetting(item, settingId):
	rowCount = ui.users.rowCount()
	settings.setValue(settingId+'.rowCount', rowCount)
	for rowIndex in range(rowCount):
		for columnIndex in range(item.columnCount()):
			if item.item(rowIndex, columnIndex):
				settings.setValue(settingId+'['+str(rowIndex)+','+str(columnIndex)+']', item.item(rowIndex, columnIndex).text())

# load ui from file
def loadUi(sfileName):
	file = QFile(os.path.join(os.getcwd(), sfileName))
	if not file.open(QIODevice.ReadOnly):
		print(f"Cannot open {sfileName}: {file.errorString()}")
		return None
	loader = QUiLoader()
	ui = loader.load(file)
	file.close()
	if not ui:
		print(loader.errorString())
		return None
	# connect signals<>slots
	ui.addUser.clicked.connect(addUser)
	ui.removeUser.clicked.connect(removeUser)
	ui.removeAllUsers.clicked.connect(removeAllUsers)
	ui.publish.clicked.connect(publish)
	ui.users.itemSelectionChanged.connect(userSelectionChanged)
	return ui

# app entry point
if __name__ == "__main__":
	app = QApplication(sys.argv)
	settings = QSettings("QuanticDream", "MaestroUI")
	ui = loadUi("CanadianChristmas.ui")
	if not ui:
		sys.exit(-1)
	# load previous settings (excluding password)
	settings = QSettings("NHolleville", "CanadianChristmas")
	readTextSetting(ui.date, "date")
	readTextSetting(ui.maxBudget, "maxBudget")
	readTextSetting(ui.smtpServer, "smtpServer")
	readTextSetting(ui.smtpPort, "smtpPort")
	readTextSetting(ui.smtpLogin, "smtpLogin")
	readTextSetting(ui.senderAddress, "senderAddress")
	readTableSetting(ui.users, "users")
	# exec
	ui.show()
	iReturnCode = app.exec_()
	# save current settings (excluding password)
	writeTextSetting(ui.date, "date")
	writeTextSetting(ui.maxBudget, "maxBudget")
	writeTextSetting(ui.smtpServer, "smtpServer")
	writeTextSetting(ui.smtpPort, "smtpPort")
	writeTextSetting(ui.smtpLogin, "smtpLogin")
	writeTextSetting(ui.senderAddress, "senderAddress")
	writeTableSetting(ui.users, "users")
	# done
	sys.exit(iReturnCode)
