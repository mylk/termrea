## termrea

A terminal RSS reader based on `liferea`.

![](docs/images/screenshot.png)

### Purpose

My favorite RSS reader is `liferea`, but I needed the terminal feeling. I love the terminal.  
The combination of the points above is what made me create `termrea`.

### How it works

This application uses two main elements of `liferea`:

- the configuration file `feedlist.opml` which contains the RSS feeds and their tree structure,
- the database `liferea.db` which contains the news items.

Also, currently the feed fetching mechanism of `liferea` is used, which means that liferea has to run  
along  with termrea. I prefer to run it on a framebuffer, instead of the actual X session.

Last but not least, currently to manage the RSS feeds (create, update, delete) you have to use `liferea`.

The only shared aspect with `liferea` that I wish to change, is to create for termrea its own feed  
fetching mechanism. The other shared aspects (the configuration file and the database), I think are  
okay and I like the idea of the applications being interchangeable.

What currently termrea does by its own:

- present the news items and navigate through them,
- present the feed sources and navigate through them,
- toggle news items between read / unread,
- mark sources and groups of sources as read,
- and, of course open news items to your browser :-)

### Run

Clone the project, head to the project's root directory and run:

```
termrea
```

### Controls

| Key     | Description                        |
| :-----: | :--------------------------------- |
| ↑ ↓ ← → | navigate                           |
| r       | read                               |
| u       | unread                             |
| f       | fetch content fetched by `liferea` |
| q       | quit                               |

### Configure

Edit `termrea/config.py` to point to the configuration file and database.  
Don't worry, the defaults are already set in there.

