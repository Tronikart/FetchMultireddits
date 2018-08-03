import requests
import json
import sys
from pymongo import MongoClient

max_posts = 5
for item in sys.argv:
    if "max" in item:
        max_posts = str(item.split(':')[1])

client = MongoClient()
db = client.subs_db

posted = db[DATABASE_NAME]
adminid = ADMIN_ID
botkey = BOTAPI_KEY
reddit_user = REDDIT_USER

def handleRedditRequest(url):
    try:
        request = requests.get(url, headers = {'User-agent': '/r/' + reddit_user})
        return {'timeout' : False, 'request' : request, 'url' : url}
    except:
        return {"timeout" : True, 'request' : ""}

def parse_reddit(data):
	return {
                'url'       : data['data']['url'], 
                'sub'       : data['data']['subreddit'],
                'title'     : data['data']['title'],
                'author'    : data['data']['author'],
                'score'     : str(data['data']['score']),
                'permalink' : "https://www.reddit.com" + data['data']['permalink']
            }

def get_next_page(data):
	return data['data']['after']

def get_prev_page(data):
	return data['data']['before']

def get_next_page_params(url):
	# Getting count number, if any
	if len(url.split('count=')) == 2:
		count = int(url.split('count=')[1].split('&')[0]) + 25
	else:
		count = 25
	# Getting current page info
	request = handleRedditRequest(url)
	data = request['request'].json() if not request['timeout'] else ""
	# If there was no error, proceed
	if data:
		after = get_next_page(data)
		# After can return None
		return {'error' : False, 'after' : after, 'count': count}
	else:
		return {'error' : True}

def format_caption(data):
	return '[' + data['title'] + '](' + data['url'] + ')\n\n__/r/' + data['sub'] + '\n\n[permalink](' + data['permalink'] + ')'


def send_album(channel, array):
    url = "https://api.telegram.org/bot" + botkey + "/sendMediagroup"
    try:
        request = requests.get(url, 
                                {
                                    "chat_id"   : channel,
                                    "media"     : json.dumps(array)
                                }
                            )
    except:
        requests.get("https://api.telegram.org/bot" + botkey + "/sendMessage", {'chat_id' : adminid , 'text' : "Error sending " + str(array)})
    
    if not request.ok:
        for link in array:
            print(link)
            url = "https://api.telegram.org/bot" + botkey + "/sendPhoto"
            payload = {
            			'chat_id' 		: channel, 
            			'photo'			: link["media"].replace("&", "%26"),
            			'caption'		: link['caption'],
            			'parse_mode'	: 'Markdown'
            }
            requests.get(url, payload)

def go_through_posts(request, max_posts, posts = 0, urls = list()):
	if 'data' in request['request'].json().keys():
		data = request['request'].json()['data']['children']
	else:
		print(request['request'].json())
	# Going through the posts until 5 are done or until finished
	for child in data:
		post = parse_reddit(child)
		if posted.find_one({'url' : post['url']}):
			continue
		else:
			posted.insert_one(post)
			urls.append({'type' : 'photo', 'media' : post['url'], 'caption' : format_caption(post), 'parse_mode' : 'Markdown'})
			posts += 1
		if posts == max_posts:
			return {'done' : True, 'urls' : urls}
	# If finished without 5, return False and posts
	return {'done' : False, 'urls' : urls, 'posts' : posts}


def fetchMulti(multi, max_posts):
	url = 'https://www.reddit.com/user/' + multi
	# Hourly top
	###################
	request = handleRedditRequest(url + 'top/.json?sort=top&t=hour')
	if not request['timeout']:
		# First page go through
		posts = go_through_posts(request, max_posts)
		if posts['done']:
			return posts['urls']
		else:
			page = get_next_page_params(request['url'])
			request = handleRedditRequest(url + 'top/.json?sort=top&t=hour&count=' + str(page['count']) + "&after=" + page['after'])
			# Second page and last page go through
			if not request['timeout']:
				posts = go_through_posts(request, max_posts, posts['posts'], posts['urls'])
				if posts['done']:
					return posts['urls']
				else:
					# Daily top
					###################
					request = handleRedditRequest(url + 'top/.json?sort=top&t=day')
					if not request['timeout']:
						#First go through
						posts = go_through_posts(request, max_posts)
						if posts['done']:
							return posts['urls']
						else:
							while True:
								# going until either done or no more next pages
								page = get_next_page_params(request['url'])
								if page['after']:
									request = handleRedditRequest(url + 'top/.json?sort=top&t=day&count=' + str(page['count']) + '&after=' + page['after'])
									if not request['timeout']:
										posts = go_through_posts(request, max_posts, posts['posts'], posts['urls'])
										if posts['done']:
											return posts['urls']
										else:
											continue
									else:
										requests.get("https://api.telegram.org/bot" + botkey + "/sendMessage", {'chat_id' : adminid, 'text' : "Fetching " + multi + " timedout."})
								else:
									break
							# Hot top
							###################
							request = handleRedditRequest(url)
							if not request['timeout']:
								# First go through
								posts = go_through_posts(request, max_posts)
								if posts['done']:
									return posts['urls']
								else:
									while True:
										# going until done or somehow no more pages
										page = get_next_page_params(request['url'])
										if page['after']:
											request = handleRedditRequest(url + '.json?count=' + str(page['count']) + '&after=' + page['after'])
											if not request['timeout']:
												posts = go_through_posts(request, max_posts, posts['posts'], posts['urls'])
												if posts['done']:
													return posts['urls']
												else:
													continue
											else:
												requests.get("https://api.telegram.org/bot" + botkey + "/sendMessage", {'chat_id' : adminid, 'text' : "Fetching " + multi + " timedout."})
										else:
											return posts['urls']
							else:
								requests.get("https://api.telegram.org/bot" + botkey + "/sendMessage", {'chat_id' : adminid, 'text' : "Fetching " + multi + " timedout."})
					else:
						requests.get("https://api.telegram.org/bot" + botkey + "/sendMessage", {'chat_id' : adminid, 'text' : "Fetching " + multi + " timedout."})
			else:
				requests.get("https://api.telegram.org/bot" + botkey + "/sendMessage", {'chat_id' : adminid, 'text' : "Fetching " + multi + " timedout."})
	else:
		requests.get("https://api.telegram.org/bot" + botkey + "/sendMessage", {'chat_id' : adminid, 'text' : "Fetching " + multi + " timedout."})


def postMulti(multi, channel, max_posts):
	urls = fetchMulti(multi, max_posts)
	requests.get("https://api.telegram.org/bot" + botkey + "/sendMessage", {'chat_id' : adminid, 'text' : "Fetching " + str(max_posts) + " posts for " + channel})
	send_album(channel, urls)




# Example 
# postMulti('Tronika/m/imaginaryideasvault/', '@channel', max_posts)
