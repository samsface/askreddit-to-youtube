import praw, subprocess, os, glob, random, re, time
from google_speech import Speech
from string import Template 

reddit = praw.Reddit(client_id='your client id',
                     client_secret='your client secret',
                     user_agent='python:botmancan:botmancan:v0.0.1 (by /u/botmancan)')

reddit_thumbnail_html = Template("""
<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Hello Bulma!</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/bulma/0.7.4/css/bulma.min.css">
    <style>
    h1 { font-size: 100px !important; }
    .subtitle { font-size: 48px !important; }
    </style>
  </head>
  <body>
  <section class="section">
    <div class="container">
      <p class="subtitle">
        <img src="https://image.flaticon.com/icons/png/512/174/174866.png" style="height:48px;margin-right:8px;transform:translate(0,4px);"></img><strong>r/$subreddit</strong> Posted by u/$author
      </p>
       <h1 class="title">
        $title 
      </h1>
      <img src="$icon" style="position:absolute;top:500px;left:150px;">
    </div>
  </section>
  </body>
</html>""")

reddit_title_html = Template("""
<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Hello Bulma!</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/bulma/0.7.4/css/bulma.min.css">
    <style>
    h1 { font-size: 76px !important; }
    .subtitle { font-size: 48px !important; }
    </style>
  </head>
  <body>
  <section class="section">
    <div class="container">
      <p class="subtitle">
        <img src="https://image.flaticon.com/icons/png/512/174/174866.png" style="height:48px;margin-right:8px;transform:translate(0,4px);"></img><strong>r/$subreddit</strong> Posted by u/$author
      </p>
       <h1 class="title">
        $title
      </h1>
    </div>
  </section>
  </body>
</html>""")

reddit_title_speech = Template("""Dear $subreddit ! $title""")

reddit_comment_html = Template("""
<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Hello Bulma!</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/bulma/0.7.4/css/bulma.min.css">
    <style>
    h1 { font-size: 76px !important; }
    .subtitle { font-size: 48px !important; }
    </style>
  </head>
  <body>
  <section class="section">
    <div class="container">
      <p class="subtitle">
        Posted by u/$author
      </p>
       <h1 class="title">
        $text
      </h1>
    </div>
  </section>
  </body>
</html>""")

reddit_comment_speech = Template("""$text""")

def make_png(name, template, args):
    output_file = '{0}.png'.format(name)
    html = template.substitute(args)
    f = open('tmp.html', 'w')
    f.write(html)
    f.close()
    subprocess.call(['cutycapt', '--min-width=1920', '--min-height=1080', '--url=file://{0}/tmp.html'.format(os.getcwd()), '--out={0}'.format(output_file)])
    return output_file

def make_wav(name, template, args):
    output_file = '{0}.mp3'.format(name)
    transcript = template.substitute(args)
    speech = Speech(transcript, random.choice(['en-UK', 'en-US', 'en-IE', 'en-ZA', 'en-NZ', 'en-KE']))
    speech.save('tmp.mp3')
    pitch = random.choice([1,2,3,4,5,6,7,8,9,10])
    subprocess.call(['sox', 'tmp.mp3', 'tmp2.wav', 'pitch', '-{}00'.format(pitch), 'speed', '1.3'.format(pitch), 'reverse'])
    subprocess.call(['sox', 'tmp2.wav', output_file, 'reverse', 'silence', '1', '00:00:01', '-96d'])
    return output_file

def combine_png_with_wav(name, png, wav):
    output_file = '{0}.mp4'.format(name)
    subprocess.call(['ffmpeg', '-loop', '1', '-i', png, '-i', wav, '-shortest', '-c:v', 'libx264', '-tune', 'stillimage', '-c:a', 'copy', output_file])
    return output_file

def make_mp4(name, html_template, speech_template, args):
    png = make_png(name, html_template, args)
    wav = make_wav(name, speech_template, args)
    mp4 = combine_png_with_wav(name, png, wav)
    return mp4

def make_thumbnail(html_template, args):
    args['icon'] = random.choice(glob.glob('../images/*'))
    png = make_png('thumb', html_template, args)
    return png

def make_video(submission):
    os.makedirs(submission['id'])
    os.chdir(submission['id'])

    thumbnail = make_thumbnail(reddit_thumbnail_html, submission)

    counter = 0

    # make title screen
    make_mp4(counter, reddit_title_html, reddit_title_speech, submission)

    counter += 1

    for comment in submission['comments']:
      make_mp4(counter, reddit_comment_html, reddit_comment_speech, comment)
      counter += 1

    # concat everything
    transitions = glob.glob('../transitions/static/*')

    inputs = []
    filters= ''
    j = 0
    for i in range(0, counter):
      inputs.append('-i')
      inputs.append('{0}.mp4'.format(i))
      inputs.append('-i')
      inputs.append('{0}'.format(transitions[0]))
      filters += '[{0}:v:0][{0}:a:0]'.format(j)
      j += 1
      filters += '[{0}:v:0][{0}:a:0]'.format(j)
      j += 1

    subprocess.call(['ffmpeg'] + inputs + ['-filter_complex', filters + 'concat=n={0}:v=1:a=1[outv][outa]'.format(len(inputs)/2), '-map', '[outv]', '-map', '[outa]', 'out.mp4'])

    # clean up
    os.rename('out.mp4',   '../{0}.mp4'.format(submission['id']))
    os.rename('thumb.png', '../{0}.png'.format(submission['id']))
    f = open('../{0}.txt'.format(submission['id']), 'w')
    f.write(submission['title'] + '\n')
    f.write('reddit,askreddit,funny,lol,stupid,karma,upvotes')
    f.close()
    subprocess.call(['rm', '-rf', '../{0}'.format(submission['id'])])

def scrape(subreddit):
    res = { 'comments': [] }

    for submission in reddit.subreddit(subreddit).hot(limit=10):
        if submission.num_comments < 10 or int(time.time()) - submission.created_utc > 86400: continue

        res['id'] = submission.id
        res['subreddit'] = subreddit
        res['author'] = submission.author
        res['title'] = submission.title
        res['text'] = sanitize(submission.selftext)
        
        i = 0
        for comment in submission.comments.list():
            if(len(comment.body) > 200): continue
            res['comments'].append({ 'author': comment.author, 'text': sanitize(comment.body) })
            i += 1
            if i == 10: break

        break

    return res


def sanitize(text):
  arrBad = [
    'add words you want to santize to this list'
  ]
  
  brokenStr1 = text.split()
  new = ''
  for word in brokenStr1:
      if word in arrBad:
          text = text.replace(word, 'BEEP')

  #text = re.sub(r'[^a-zA-Z0-9_\.,\' \?]+', '', text)

  return text

if  __name__ =='__main__':
    make_video(scrape('askmen'))
