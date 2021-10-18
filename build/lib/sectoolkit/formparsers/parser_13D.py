from bs4 import BeautifulSoup
import unicodedata
import numpy as np
import re


class parser_13D(object):

	def __init__(self, file_body):
		self.body = file_body
		self.cleanedText = ''
		self.itemCutoffs = ''
		self.processedText = ''

	def _cleanFileText(self):
			
		text = self.body.get_text()
		
		text = unicodedata.normalize("NFKD", text)
		text = re.sub(r'\n+', '\n',text)
		text = re.sub(r'\n +', '\n',text)
		text = re.sub(r'\n+', '\n',text)
		text = re.sub(r' +', ' ',text)
	#     text = re.sub(r"&nbsp;", " ", text)
	#     text = re.sub(r"\n", " ", text)
		pattern = re.compile(r"(?i)^(Item [1-7]?[.])\s", re.M)
		text = re.sub(pattern, r'\1 ', text)
		# Addition: Dec 18, 2018 or so
		add_the = re.compile(r"(?i)^(Item 5. Interest in Securities of Issuer)\.?", re.M)
		text = re.sub(add_the, r'Item 5. Interest in Securities of the Issuer.', text)
		# Remove page numbering footers if present
		text = re.sub(r'page \d+ of \d+ ', ' ', text, flags = re.IGNORECASE|re.M)

		self.cleanedText = text
		
		
	def _findItems(self):
		
		if self.cleanedText == '':
			self._cleanFileText()

		text = self.cleanedText

		# The first item is the document length
		Items = [0, 0, 0, 0, 0, 0, 0, 0, 0]
		Items[0] = len(text) 
		it = [0, 0, 0, 0, 0, 0, 0, 0, 0]

		#Item 1. Security and Issuer. 
		it = [[m.start(), m.end()] for m in \
			   re.finditer(r"(?i)^Item[^1]?1[^r'Security']*Security[^r'and']*and[^r'Issuer']*Issuer[ \s.]?",text,re.M|re.S)]

		if it:
			#print('1',text[it[0][0]:it[0][1]])
			text = text[:it[0][0]-1]+'\n\n_Item 1_ Security and Issuer.\n\n'+text[it[0][1]:]
			#print('1',text[it[0][0]-20:it[0][1]+20])
			Items[1] = it[0][0]
		else:
			Items[1] = 0

		# Item 2. Identity and Background. 
		it = [[m.start(), m.end()] for m in \
			   re.finditer(r"(?i)^Item[^2]?2[^r'Identity']*Identity[^r'and']*and[^r'Background']*Background[ \s.]?",text,re.M|re.S)]

		if it:
			#print('2',text[it[0][0]:it[0][1]])
			text = text[:it[0][0]-1]+'\n\n_Item 2_ Identity and Background.\n\n'+text[it[0][1]:]
			#print('2',text[it[0][0]-20:it[0][1]+20])
			Items[2] = it[0][0]
		else:
			Items[2] = 0  

		# Item 3. Source and Amount of Funds or Other Consideration. 
		it = [[m.start(), m.end()] for m in \
			   re.finditer(r"(?i)^Item[^3]?3[^r'Source']*Source[^r'and']*and[^r'Amount']*Amount[^r'of']*of[^r'Funds']*Funds[^r'or']*or[^r'Other']*Other[^r'Consideration']*Consideration[ \s.]?",text,re.M|re.S)]

		if it:
			#print('3',text[it[0][0]:it[0][1]])
			text = text[:it[0][0]-1]+'\n\n_Item 3_ Source and Amount of Funds or Other Consideration.\n\n'+text[it[0][1]:]
			#print('3',text[it[0][0]-20:it[0][1]+20])
			Items[3] = it[0][0]
		else:
			Items[3] = 0          

		# Item 4. Purpose of Transaction.  
		it = [[m.start(), m.end()] for m in \
			   re.finditer(r"(?i)^Item[^4]?4[^r'Purpose']*Purpose[^r'of']*of[^r'Transaction']*Transaction[ \s.]?",text,re.M|re.S)]

		if it:
			#print('4',text[it[0][0]:it[0][1]])
			text = text[:it[0][0]-1]+'\n\n_Item 4_ Purpose of Transaction.\n\n'+text[it[0][1]:]
			#print('4',text[it[0][0]-20:it[0][1]+20])
			Items[4] = it[0][0]
		else:
			Items[4] = 0  

		# Item 5. Interest in Securities of the Issuer.    
		it = [[m.start(), m.end()] for m in \
			   #re.finditer(r"^(?i)Item[^5]?5[^r'Interest']*Interest[^r'in']*in[^r'Securities']*Securities[^r'of']*of[^r'the']*the[^r'Issuer']*Issuer[ \s.]?",text,re.M|re.S)]
			   re.finditer(r"(?i)^Item[^5]?5[^r'Interest']*Interest[^r'in']*in[^r'Securities']*Securities[^r'of']*of[^r'the']*the[^r'Issuer']*Issuer[ \s.]?",text,re.M|re.S)]

		if it:
			#print('5',text[it[0][0]:it[0][1]])
			text = text[:it[0][0]-1]+'\n\n_Item 5_ Interest in Securities of the Issuer.\n\n'+text[it[0][1]:]
			#print('5',text[it[0][0]-20:it[0][1]+20])
			Items[5] = it[0][0]
		else:
			Items[5] = 0      

		# Item 6. Contracts, Arrangements, Understandings or Relationships With Respect to Securities of the Issuer.    
		it = [[m.start(), m.end()] for m in \
			   re.finditer(r"(?i)^Item[^6]?6[^r'Contracts,']*Contracts,[^r'Arrangements,']*Arrangements,[^r'Understandings']*Understandings[^r'or']*or[^r'Relationships']*Relationships[^r'with']*with[^r'respect']*respect[^r'to']*to[^r'Securities']*Securities[^r'of']*of[^r'the']*the[^r'Issuer']*Issuer[ \s.]?",text,re.M|re.S)]

		if it:
			#print('6',text[it[0][0]:it[0][1]])
			text = text[:it[0][0]-1]+'\n\n_Item 6_ Contracts, Arrangements, Understandings or Relationships With Respect to Securities of the Issuer.\n\n'+text[it[0][1]:]
			#print('6',text[it[0][0]-20:it[0][1]+20])
			Items[6] = it[0][0]
		else:
			Items[6] = 0   

		# Item 7. Material to be Filed as Exhibits.    
		it = [[m.start(), m.end()] for m in \
			   re.finditer(r"(?i)^Item[^7]?7[^r'Material']*Material[^r'to']*to[^r'be']*be[^r'Filed']*Filed[^r'as']*as[^r'Exhibits']*Exhibits[ \s.]?",text,re.M|re.S)]

		if it:
			#print('7',text[it[0][0]:it[0][1]])
			text = text[:it[0][0]-1]+'\n\n_Item 7_ Material to be Filed as Exhibits.\n\n'+text[it[0][1]:]
			#print('7',text[it[0][0]-20:it[0][1]+20])
			Items[7] = it[0][0]
		else:
			Items[7] = 0   

		# Signature: pick the first token after the last item
		it = [[m.start(), m.end()] for m in re.finditer(r"(?i)^Signature[s \s.]?",text, re.M|re.S)]
		if it:
			#print (it, len(it))
			if len(it) == 1:
				Items[8] = it[0][0]
				text = text[:it[0][0]-1]+'\n\n_Signature/s_ .\n\n'+text[it[0][1]:]

			else:
				found = 0
				for i in range(len(it)):
					if (it[i][0] > max(Items[1:7])) and (found == 0):
						Items[8] = it[i][0]
						text = text[:it[i][0]-1]+'\n_Signature/s_ .\n'+text[it[i][1]:]
						found = 1
			#print(text[Items[8]:Items[8]+30])                          
		else:
			Items[8] = 0

		self.itemCutoffs = np.asarray(Items)
		self.processedText = text


	def _get_item(self, itemNumber):

		if itemNumber == 0:
			return self.body.get_text()

		else:
			if len(self.itemCutoffs) == 0:
				self._findItems()

			if itemNumber + 1 <= len(self.itemCutoffs):
				end = itemNumber + 1
			else:
				end = self.itemCutoffs[0]

			item = self.processedText[self.itemCutoffs[itemNumber]:self.itemCutoffs[end]].replace('\n', ' ')

			if len(item) != 0:
				return item.strip()
			else:
				return "No Item {} found in this filing.".format(itemNumber)


	def parse(self):
		parsed = {}
		for itemnum in range(1,8):
			parsed['item_'+str(itemnum)] = self._get_item(itemnum)
		return parsed