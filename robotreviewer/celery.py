from celery import Celery

app = Celery('robotreviewer',
             broker='amqp://',
             backend='amqp://',
             include=['robotreviewer.annotator_worker'])

# Optional configuration, see the application user guide.
app.conf.update(
    result_expires=3600,
)



if __name__ == '__main__':
    app.start()