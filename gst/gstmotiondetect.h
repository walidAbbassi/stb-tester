/* Gstreamer element for motion detection (not motion tracking) using OpenCV.
 *
 * Copyright (C) 2012 YouView TV Ltd.
 * Author: David Rothlisberger <david@rothlis.net>
 *
 * This library is free software; you can redistribute it and/or
 * modify it under the terms of the GNU Lesser General Public
 * License as published by the Free Software Foundation; either
 * version 2.1 of the License, or (at your option) any later version.
 *
 * This library is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * Lesser General Public License for more details.
 */

#ifndef __GST_MOTIONDETECT_H__
#define __GST_MOTIONDETECT_H__

#include <gst/gst.h>
#include <gst/base/gstbasetransform.h>

G_BEGIN_DECLS

#define GST_TYPE_MOTIONDETECT \
  (gst_motiondetect_get_type())
#define GST_MOTIONDETECT(obj) \
  (G_TYPE_CHECK_INSTANCE_CAST((obj),GST_TYPE_MOTIONDETECT,GstMotionDetect))
#define GST_MOTIONDETECT_CLASS(klass) \
  (G_TYPE_CHECK_CLASS_CAST((klass),GST_TYPE_MOTIONDETECT,GstMotionDetectClass))
#define GST_IS_MOTIONDETECT(obj) \
  (G_TYPE_CHECK_INSTANCE_TYPE((obj),GST_TYPE_MOTIONDETECT))
#define GST_IS_MOTIONDETECT_CLASS(klass) \
  (G_TYPE_CHECK_CLASS_TYPE((klass),GST_TYPE_MOTIONDETECT))

typedef struct _GstMotionDetect GstMotionDetect;
typedef struct _GstMotionDetectClass GstMotionDetectClass;

/**
 * GstMotionDetect:
 *
 * Opaque data structure
 */
struct _GstMotionDetect {
  GstBaseTransform element;

  gboolean enabled;
};

struct _GstMotionDetectClass {
  GstBaseTransformClass parent_class;
};

GType gst_motiondetect_get_type(void);

G_END_DECLS

#endif /* __GST_MOTIONDETECT_H__ */
