#Utility to scrape digitalcommons@wayne.edu, get paper of the day, and email author
# coding: utf-8

import os
import sys
from bs4 import BeautifulSoup, SoupStrainer
import re
import requests
import json
import urllib
import smtplib
import ast
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


# CONFIGURATIONS
########################################################################
# base url for digital commons front-page where POTD exists
digital_commons_url = "http://digitalcommons.wayne.edu"
# base url for Solr
solr_base_url = "http://localhost/solr4/DCArchive/select?"
# email configurations
me = "scholarscooperative@wayne.edu"
cc = "scholarscooperative@wayne.edu"
########################################################################


# global object
emailObj = {}


# scrape digitalcommons.wayne for POD title
def scrapeTitle():

	# grab page
	r = requests.get(digital_commons_url)
	html_doc = r.text

	# place page into BeautifulSoup object
	soup = BeautifulSoup(html_doc)

	for each_div in soup.findAll('div',{'class':'box potd'}):
		title = each_div.a.next_element

	return title


# query Solr for author name and department
def solrSearch(title):		
	
	# massage title string	
	titleOrig = title	
	title = title.encode('utf8') 
	print title
	title = '"'+title+'"'

	solrParams = {}
	solrParams['wt'] = "python"
	solrParams['indent'] = "true"
	solrParams['q'] = title
	solrParams['fl'] = "email coverpage-url"		

	solrParamsString = urllib.urlencode(solrParams)
	print "Query String: ",solrParamsString

	# make Solr Request
	r = requests.get(solr_base_url+solrParamsString)				
	response = r.text	

	print "Query Response:",response	
	emailObj['solrResponse'] = response
	responseDict = ast.literal_eval(response)

	# return the goods
	if responseDict['response']['numFound'] != 0 and 'email' in responseDict['response']['docs'][0]:
		print responseDict['response']['docs']		
		emails = responseDict['response']['docs'][0]['email']		
		article_link = responseDict['response']['docs'][0]['coverpage-url'][0]
		return {'emails':emails,'article_link':article_link}
	else:
		print "Article not found in Solr, or no emails present. Reporting, exiting."
		filename = "errors.txt"
		fhand = open(filename,"a")
		# fhand.write("\nArticle not found in Solr, or no emails present, '{titleOrig}'".format(titleOrig=titleOrig))
		fhand.close()
		exit()


# email author
def emailAuthor(email,article_link,title,):		
	
	recipients = []
	recipients.append(email)		
		
	# you = ", ".join(recipients)
	you = email	

	# Create message container - the correct MIME type is multipart/alternative.
	msg = MIMEMultipart('alternative')
	msg['Subject'] = "Your Paper has been selected for DigitalCommons@WayneState Paper of the Day!"
	msg['From'] = me
	msg['To'] = you	
	msg['BCC'] = cc

	# Create the body of the message (a plain-text and an HTML version).
	text = "Congratulations!\nYour article in DigitalCommons@WayneState has been selected for 'Paper of the Day'!"
	html = """
	<html>
	<head>
	<title>DC@WSU Paper of the Day</title>
	<style type="text/css">
	.style2 
	{{
		font-family:"Verdana", Verdana, sans-serif;	
		font-size: 14px 
	}}
	body {{
		background-color: #007363;
	}}	
	</style>
	</head>

	<body>
	<table width="600" border="0" align="center" cellpadding="0" cellspacing="0">
	  <tr>
	    <td width="600"><table width="600" border="0" cellspacing="0" cellpadding="0">
	      <tr>
	        <td width="600"><img src="http://www.lib.wayne.edu/resources/digital/dc/logos/white_background_800wide.gif" width="600" /></td>
	      </tr>
	      <tr>
	        <td bgcolor="#FFFFFF">
		  <br /><div style="padding-left: 1em; padding-right: 1em;">
	          
		  <p align="justify" class="style2">We thought you would like to know that your work, "<a href='{article_link}'><b>{title}</b></a>," is being featured as today's "Paper of the Day" in <a href="http://digitalcommons.wayne.edu">DigitalCommons@WayneState</a>.</p>
		  <p align="justify" class="style2">Your work is highlighted on the front page of <a href="http://digitalcommons.wayne.edu">DC@WSU</a>.  Take a look and see it for yourself!</p>
	 	  <p align="justify" class="style2">Are you currently a Wayne State author, and interested in making more of your publications more widely available? It's simple: just send us your CV for review, and we will provide you with a full report of which works we can deposit into DC@WSU for you.</p>
		  <p align="justify" class="style2">If you have any questions, please don't hesitate to contact us.</p>
		  <p align="justify" class="style2">The Scholars Cooperative @ Wayne State University Library System<br />
		  <a href="http://scholarscooperative.wayne.edu">scholarscooperative.wayne.edu</a><br />
		  <a href="mailto:scholarscooperative@wayne.edu">scholarscooperative@wayne.edu</a>
		</div><br />
		</p></td>
	      </tr>
	      <tr>
	        <td width="600"><img src="http://www.lib.wayne.edu/resources/digital/dc/logos/footer_logos_800wide.png" width="600" /></td>
	      </tr>	
	    </table></td>
	  </tr>
	</table>
	</body>
	</html>
	""".format(title=title.encode('utf8'),article_link=article_link)
	

	# Record the MIME types of both parts - text/plain and text/html.
	part1 = MIMEText(text, 'plain')
	part2 = MIMEText(html, 'html')

	# Attach parts into message container.
	# According to RFC 2046, the last part of a multipart message, in this case
	# the HTML message, is best and preferred.
	msg.attach(part1)
	msg.attach(part2)

	# Send the message via local SMTP server.	
	s = smtplib.SMTP('mail.wayne.edu')
	# sendmail function takes 3 arguments: sender's address, recipient's address
	# and message to send - here it is sent as one string.	
	s.sendmail(me, [you,cc], msg.as_string())	
	s.quit()	
	print "Email successfully sent to",you


def PODemail():
	##############################################################################
	# TESTING TITLE
	# title = "Enter article title to test on here..."			
	##############################################################################
	##############################################################################
	# LIVE ARTICLE EMAILER
	title = scrapeTitle()	
	##############################################################################	

	# get emails
	return_package = solrSearch(title)
	emails = return_package['emails']
	article_link = return_package['article_link']
	for email in emails:		
		try:			
			emailAuthor(email,article_link,title)
		except:
			print "Can't email"
			filename = "errors.txt"
			fhand = open(filename,"a")
			fhand.write("\n{email}".format(email=email))
			fhand.close()

if __name__ == "__main__":
	PODemail()



















