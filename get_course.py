from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from multiprocessing import Process as P
from multiprocessing import Queue as Q
import selenium.webdriver.support.ui as ui
import os,shutil,time,sqlite3,json

# configuration
os.chdir("/Users/Martin-Bao/Documents/CourseSearch") # add only running in subime REPL
threads = 3

# utilities
rtime = lambda start_time:"["+str(round(time.time()-start_time,2))+"sec]"
wait = lambda x:ui.WebDriverWait(driver,5).until(lambda y:x)
gmt = lambda :':'.join([str(i) for i in time.gmtime()[:6]])
def load(threadno):
	while True:
		try:
			if not driver[threadno].find_element_by_id("WAIT_win0").is_displayed():
				break
		except:
			pass

# main defs
def initialize():
	global driver,p,cursor_db,db
	driver = [webdriver.Chrome("/Users/Martin-Bao/Documents/CourseSearch/chromedriver") for i in range(threads)]
	# driver = [webdriver.PhantomJS("/Users/Martin-Bao/Documents/CourseSearch/phantomjs") for i in range(threads)]
	start_time = time.time()
	p = [P(target=login,args=(i,)) for i in range(threads)]
	[i.start() for i in p]
	[i.join() for i in p]
	print("Initialized Successfully",rtime(start_time))
def quitall():
	for d in driver:
		d.quit()
def login(threadno):
	start_time = time.time()
	d = driver[threadno]
	d.get("https://admin.portal.nyu.edu/psp/paprod/EMPLOYEE/EMPL/?cmd=logout")
	d.get("https://admin.portal.nyu.edu/psp/paprod/EMPLOYEE/CSSS/c/SA_LEARNER_SERVICES.SSS_STUDENT_CENTER.GBL?FolderPath=PORTAL_ROOT_OBJECT.NYU_STUDENT_CTR&IsFolder=false&IgnoreParamTempl=FolderPath%2cIsFolder")
	wait(d.find_element_by_id("userid")).send_keys("pb1713")
	wait(d.find_element_by_id("pwd")).send_keys("042800@efZ"+Keys.ENTER)
	d.switch_to_frame(wait(d.find_element_by_name("TargetContent")))
	wait(d.find_element_by_id("DERIVED_SSS_SCL_SSS_GO_4$83$")).click()
	load(threadno)
	print("Thread "+str(threadno)+" Initialized Successfully",rtime(start_time))
def update_dict(threadno=0):
	start_time = time.time()
	d = driver[threadno]
	os.remove('dict.db') if os.path.exists('dict.db') else None
	open('dict.db','w').close()
	dict = sqlite3.Connection('dict.db')
	cursor_dict = dict.cursor()
	dict_temp = []
	table = d.find_element_by_id("ACE_GROUP$0").find_elements_by_xpath("tbody/tr")[1:]
	campuses = {}
	for t in table:
		campus_name = t.find_element_by_xpath("td/div/table/tbody/tr/td/div/a[1]").get_attribute("innerHTML")
		campus_name = campus_name[campus_name.index("Collapse section")+17:-38]
		campuses[campus_name] = t
	cursor_dict.execute("CREATE TABLE Campuses (Campuses)")
	cursor_dict.executemany("INSERT INTO Campuses VALUES(?)",[[c] for c in campuses])
	for c in campuses:
		subject_str = campuses[c].find_element_by_xpath("td/div/table/tbody/tr[2]").text
		campus_name = c
		while subject_str != '':
			subject_name = ' '.join(subject_str[:subject_str.index('(')].split())
			subject_code = subject_str[subject_str.index('(')+1:subject_str.index(')')]
			subject_search_code = subject_code if not "_" in subject_code else subject_code[:subject_code.index("_")]
			subject_str = subject_str[subject_str.index(')')+1:]
			dict_temp.append([subject_code,subject_search_code,campus_name,subject_name])
	cursor_dict.execute("CREATE TABLE Main (subject_code,subject_search_code,campus_name,subject_name)")
	cursor_dict.executemany("INSERT INTO Main VALUES(?,?,?,?)",dict_temp)
	dict.commit()
	dict.close()
	print("Dictionary Updated Successfully",rtime(start_time))
def update_data(wipe_data=0):
	global subjects,dict,cursor_dict,db,cursor_db
	start_time = time.time()
	if wipe_data == 1:
		
	dict = sqlite3.Connection('dict.db')
	cursor_dict = dict.cursor()
	cursor_dict.execute("SELECT * FROM Main")
	subjects = cursor_dict.fetchall()
	for i in range(len(subjects)):
		while sum([p[t].is_alive() for t in range(threads)]) == threads:
			pass
		for t in range(threads):
			if not p[t].is_alive():
				p[t] = P(target=update_subject,args=(i,t,interval,q))
				p[t].start()
				break
	[p[t].join() for t in range(threads)]
	while not q.empty():
		pass
	print("Database Updated Successfully",rtime(start_time))
	db.close()
	dict.close()
	p1.terminate()
	quitall()
def update_subject(i,threadno,interval,q):
	start_time = time.time()
	while open("busy",'r').readline == "1":
		pass
	cursor_db.execute("SELECT update_time FROM Info WHERE course_code='"+subjects[i][0]+"'")
	if not check_update(cursor_db.fetchone()[0],interval):
		print(str(i+1)+"/"+str(len(subjects))+" Up to Date",rtime(start_time))
		return
	d = driver[threadno]
	load(threadno)
	d.find_element_by_xpath("//*[text()[contains(.,'"+subjects[i][0]+"')]]").click()
	load(threadno)
	for c in range(len(d.find_elements_by_xpath("//*[@id='ACE_$ICField3$0']/tbody/tr"))):
		course = d.find_element_by_xpath("//*[@id='ACE_$ICField3$0']/tbody/tr["+str(c+1)+"]")
		if "Click here to learn more:" in course.text:
			course.find_element_by_class_name("PSHYPERLINK").click()
			load(threadno)
	for c in d.find_elements_by_xpath("//*[contains(text(),'more description for')]"):
		c.click()
	for c in d.find_elements_by_xpath("//*[@id='ACE_$ICField3$0']/tbody/tr"):
		text = c.text
		if "Click here to learn more:" in text:
			c = c.find_element_by_xpath("td[2]/div/table/tbody/tr/td/table/tbody")
			course_campus = subjects[i][2]
			course_subject = subjects[i][3]
			c1 = c.find_element_by_xpath("tr[2]/td/div/div/span")
			c1_0 = c1.find_element_by_xpath("b").text
			course_code = " ".join(c1_0.split()[:2])
			course_name = c1_0[c1_0.index(course_code)+len(course_code)+1:]
			try:
				c1_1 = c1.find_element_by_xpath("div[2]/p").text
			except:
				c1_1 = c1.find_element_by_xpath("p").text
			try:
				course_description = c1_1[:c1_1.index("less description for")-1]
			except:
				course_description = c1_1
			c2 = c.find_element_by_xpath("tr[4]/td/div/table/tbody")
			c2_0 = c2.find_element_by_xpath("tr[1]/td/div").text
			course_terms = c2_0[c2_0.index("Terms Offered:")+15:].strip()
			course_more_info = c2.find_element_by_xpath("tr[2]/td/table/tbody/tr[2]/td/div/table/tbody").text
			q.put(("INSERT INTO Main VALUES(?,?,?,?,?,?,?)",[course_code,course_name,course_campus,course_terms,course_subject,course_description,course_more_info]))
	d.find_element_by_id("NYU_CLS_DERIVED_BACK").click()
	q.put(("UPDATE Info SET update_time = ? WHERE course_code='"+subjects[i][0]+"'",[gmt()]))
	print(str(i+1)+"/"+str(len(subjects))+" Updated Successfully",rtime(start_time))
	load(threadno)


initialize()
# update_dict()
update_data(1)