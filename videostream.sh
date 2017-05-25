v4l2-ctl --set-fmt-video=width=800,height=600,pixelformat=5
v4l2-ctl -c sharpness=30

cvlc    --no-audio \
        v4l2:///dev/video0 \
        --v4l2-width 800 \
        --v4l2-height 600 \
        --v4l2-chroma MJPG \
        --v4l2-hflip 1 \
        --v4l2-vflip 1 \
        --sout '#standard{access=http{mime=multipart/x-mixed-replace;boundary=--7b3cc56e5f51db803f790dad720ed50a},mux=mpjpeg,dst=:8080/}' \
        -I dummy
