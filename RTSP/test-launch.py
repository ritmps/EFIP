import gi

gi.require_version('Gst', '1.0')
gi.require_version('GstRtspServer', '1.0')
from gi.repository import GLib, Gst, GstRtspServer

Gst.init(None)

import argparse
parser = argparse.ArgumentParser(description='GStreamer RTSP server test-launch')
parser.add_argument('-p', '--port', default="8554", help='server port (defaults to "8554")')
parser.add_argument('-m', '--mount', default="/test", help='mount point (defaults to "/test")')
parser.add_argument('pipeline', help='GStreamer pipeline', nargs='+')
args = parser.parse_args()

port = args.port
mount = args.mount
pipeline = ' '.join(args.pipeline)

server = GstRtspServer.RTSPServer()
server.service = port
mounts = server.get_mount_points()
factory = GstRtspServer.RTSPMediaFactory()
factory.set_launch(pipeline)
factory.set_shared(True)
mounts.add_factory('/test', factory)
server.attach()

print('stream ready at rtsp://127.0.0.1:%s%s' % (port, mount))

loop = GLib.MainLoop()
loop.run()