# FetchMultireddits
Python code that fetchs from top posts on a multireddit and posts to telegram channels using mongodb to store previously posted images

As mongodb is used, `pymongo` is required to be able to run, however it wouldnt be hard to switch from this to a simple json file.

## How to run

Replace the first 4 variables with the needed information

`posted` needs a database name, this can be whatever string you'd like

`adminid` needs your Telegram ID so the bot you'll use to post these can tell you if something goes wrong.

`botkey` the API key for said bot.

`reddit_user` reddit needs to know who accesses their page, otherwise requests will return 429

Either setup cronjob with the file or execute it manually, it _shouldn't_ break, but I have it to post 5 every 30 mins so I dont know what happens when everything runs out, if this happens to you before it happens to me and you can fix it, please do.

Needless to say, the bot needs to be set as admin on the channel, otherwise it won't work.

There's an example on how to request the posts but just in case, just use `postMulti( MULTI_URL, CHANNEL, MAX_POSTS)` where MULTI_URL is the url of the multisubreddit you're wishing to fetch, the url __must not__ include the `/user/` part, so everything after that and __no__ parameters after the multisub name, CHANNEL is of course either the ID of the channel or the user, MAX_POSTS is the integer of the amount of posts you want to post.
