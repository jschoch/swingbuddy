swingbuddy!

You'll also want the sport2d server i've forked.

Pipelines are added by putting a file in the pipes directory.  Look at normalize_x_y.py for example.



run the frame generation tests: `PS C:\Users\schoch\Documents\dev\QT_UI\sim_buddy_ui\simbuddy> poetry run python -m unittest test.test_video_playback.TestVideoPlayBack.test_load_frame`


run pipeline tests:

`poetry run python .\test_pipes.py`
