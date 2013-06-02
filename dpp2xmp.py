from __future__ import division

import math
import exiftool
import glob
import pprint
import re

# http://www.exiv2.org/tags-xmp-crs.html
# http://wwwimages.adobe.com/www.adobe.com/content/dam/Adobe/en/devnet/xmp/pdfs/cs6/XMPSpecificationPart2.pdf
# http://www.sno.phy.queensu.ca/~phil/exiftool/TagNames/CanonVRD.html
# http://www.adobe.com/content/dam/Adobe/en/devnet/xmp/pdfs/XMPSpecificationPart1.pdf


class Image(object):
    def __init__(self, height, width, orientation):
        self.height = height
        self.width = width
        self.orientation = orientation

        self.cropTop = 0
        self.cropLeft = 0
        self.cropHeight = 0
        self.cropWidth = 0
        self.cropDegrees = 0
        self.hasCrop = 0

    def cropDpp(self, top, left, height, width, degrees):
        self.cropTop = top
        self.cropLeft = left
        self.cropHeight = height
        self.cropWidth = width
        self.cropDegrees = degrees

    def getXMPCrop(self):
        # rotate -45 to 45 degrees (True angle opposite sign from UI)
        # uses basic formula for translating to polar coordinates, setting the
        # angle, then translating back.
        #[[ *** formula from Steve Sprengel
        # ref:  http://feedback.photoshop.com/photoshop_family/topics/lightroom_
        # camera_raw_dng_xmp_what_is_the_formula_for_converting_crop_coordinates
        # _when_photo_gets_angled
        # ref2:
        # http://answers.yahoo.com/question/index?qid=20100314163944AAIu9xk
        # x_prime = x * Cos(theta) - y * Sin(theta) + a
        # y_prime = x * Sin(theta) + y * Cos(theta) + b
        #]]

        # fractional
        sin = math.sin(math.radians(self.degrees))
        cos = math.cos(math.radians(self.degrees))

        bottomInPixels = self.cropTop + self.cropHeight
        rightInPixels = self.cropLeft + self.cropWidth

        # x, y -> coordinates, in pixels, of upper l corner of crop box,
        #  relative to center of crop box (and hence, center of rotation).
        xUpperLeft = -self.cropWidth / 2
        yUpperLeft = -self.cropHeight / 2
        xLowerRight = self.cropWidth / 2
        yLowerRight = self.cropHeight / 2

        # xT, yT -> angled coordinates, transformed according to angle, but
        # still relative to center of rotation/crop-box.
        xUpperLeftT = xUpperLeft * cos - yUpperLeft * sin
        yUpperLeftT = xUpperLeft * sin + yUpperLeft * cos
        xLowerRightT = xLowerRight * cos - yLowerRight * sin
        yLowerRightT = xLowerRight * sin + yLowerRight * cos

        # xP, yP -> angled coordinates, in pixels, relative to upper l corner
        # of image.
        cropLeftPixelsP = self.cropLeft + (xUpperLeftT - xUpperLeft)
        cropTopPixelsP = self.cropTop + (yUpperLeftT - yUpperLeft)
        cropRightPixelsP = rightInPixels + (xLowerRightT - xLowerRight)
        cropBottomPixelsP = bottomInPixels + (yLowerRightT - yLowerRight)

        # final coordinates, as fractional values.
        left = cropLeftPixelsP / self.width
        top = cropTopPixelsP / self.height
        right = cropRightPixelsP / self.width
        bottom = cropBottomPixelsP / self.height

        if top < 0:
            bottom = bottom - top # add t differential to b
            top = 0
        if left < 0:
            right = right - left # add differential to maintain width.
            left = 0
        if bottom > 1:
            top = top - (bottom - 1)
            if top < 0:
                top = 0
            bottom = 1
        if right > 1:
            left = left - (right - 1)
            if left < 0:
                left = 0
            right = 1
        if top > bottom:
            top, bottom = bottom, top
        if left > right:
            left, right = right, left
        return top, left, bottom, right


ORIENTATION_MAPPINGS = {
    1: 'Horizontal (normal)',
    2: 'Mirror horizontal',
    3: 'Rotate 180',
    4: 'Mirror vertical',
    5: 'Mirror horizontal and rotate 270 CW',
    6: 'Rotate 90 CW',
    7: 'Mirror horizontal and rotate 90 CW',
    8: 'Rotate 270 CW',
}


FIELDS = set(re.split('\s+', '''tiff:Make
   tiff:Model
   tiff:Orientation
   tiff:ImageWidth
   tiff:ImageLength
   exif:ExifVersion
   exif:ExposureTime
   exif:ShutterSpeedValue
   exif:FNumber
   exif:ApertureValue
   exif:ExposureProgram
   exif:ExposureBiasValue
   exif:MaxApertureValue
   exif:MeteringMode
   exif:FocalLength
   exif:CustomRendered
   exif:ExposureMode
   exif:WhiteBalance
   exif:SceneCaptureType
   exif:FocalPlaneXResolution
   exif:FocalPlaneYResolution
   exif:FocalPlaneResolutionUnit
   exif:DateTimeOriginal
   exif:PixelXDimension
   exif:PixelYDimension
   dc:format
   aux:SerialNumber
   aux:LensInfo
   aux:Lens
   aux:ImageNumber
   aux:FlashCompensation
   aux:OwnerName
   aux:Firmware
   xmp:ModifyDate
   xmp:CreateDate
   xmp:MetadataDate
   xmp:Rating
   photoshop:DateCreated
   xmpMM:DocumentID
   xmpMM:OriginalDocumentID
   xmpMM:InstanceID'''))

PICTURE_STYLES = {
    0: 'Standard',
    1: 'Portrait',
    2: 'Landscape',
    3: 'Neutral',
    4: 'Faithful',
    5: 'Monochrome',
    6: 'Unknown?',
    7: 'Custom',
}


WHITE_BALANCE_MAPPINGS = {
    0: 'As Shot',
    1: 'Daylight',
    2: 'Cloudy',
    3: 'Tungsten',
    4: 'Fluorescent',
    5: 'Flash',
    8: 'Shade',
    9: 'Custom',
    30: 'Custom',
    31: 'As Shot',
    'Auto': 'As Shot',
    'Daylight': 'Daylight',
    'Cloudy': 'Cloudy',
    'Tungsten': 'Tungsten',
    'Fluorescent': 'Flourescent',
    'Flash': 'Flash',
    'Shade': 'Shade',
    'Kelvin': 'Custom',
    'Manual (Click)': 'Custom',
    'Shot Settings': 'As Shot',
}

CRS = {
    'AlreadyApplied': {'type': bool, 'values': [False, True], 'default': False},
    'AutoLateralCA': {'type': int, 'values': [False, True], 'default': False},
    'CameraProfileDigest': {
        'type': str,
        'values': ['9C057227216BE688434471F22E5E736D'],
        'default': '9C057227216BE688434471F22E5E736D'
    },
    'ColorNoiseReductionDetail': {
        'type': int, 'values': [-100, 100], 'default': 50},
    'ConvertToGrayscale': {'type': int, 'values': [-100, 100], 'default': 0},
    'CropConstrainToWarp': {'type': int, 'values': [-100, 100], 'default': 0},
    'DefringeGreenAmount': {'type': int, 'values': [-100, 100], 'default': 0},
    'DefringeGreenHueHi': {'type': int, 'values': [-100, 100], 'default': 60},
    'DefringeGreenHueLo': {'type': int, 'values': [-100, 100], 'default': 40},
    'DefringePurpleAmount': {'type': int, 'values': [-100, 100], 'default': 0},
    'DefringePurpleHueHi': {'type': int, 'values': [-100, 100], 'default': 30},
    'DefringePurpleHueLo': {'type': int, 'values': [-100, 100], 'default': 70},
    'GrainAmount': {'type': int, 'values': [-100, 100], 'default': 0},
    'HueAdjustmentAqua': {'type': int, 'values': [-100, 100], 'default': 0},
    'HueAdjustmentBlue': {'type': int, 'values': [-100, 100], 'default': 0},
    'HueAdjustmentGreen': {'type': int, 'values': [-100, 100], 'default': 0},
    'HueAdjustmentMagenta': {'type': int, 'values': [-100, 100], 'default': 0},
    'HueAdjustmentOrange': {'type': int, 'values': [-100, 100], 'default': 0},
    'HueAdjustmentPurple': {'type': int, 'values': [-100, 100], 'default': 0},
    'HueAdjustmentRed': {'type': int, 'values': [-100, 100], 'default': 0},
    'HueAdjustmentYellow': {'type': int, 'values': [-100, 100], 'default': 0},
    'LensManualDistortionAmount': {
        'type': int, 'values': [-100, 100], 'default': 0},
    'LensProfileChromaticAberrationScale': {
        'type': int, 'values': [-100, 100], 'default': 0},
    'LensProfileDigest': {'type': int, 'values': [-100, 100], 'default': 0},
    'LensProfileDistortionScale': {
        'type': int, 'values': [-100, 100], 'default': 0},
    'LensProfileEnable': {'type': int, 'values': [-100, 100], 'default': 0},
    'LensProfileFilename': {'type': int, 'values': [-100, 100], 'default': 0},
    'LensProfileName': {'type': int, 'values': [-100, 100], 'default': 0},
    'LensProfileSetup': {'type': int, 'values': [-100, 100], 'default': 0},
    'LensProfileVignettingScale': {
        'type': int, 'values': [-100, 100], 'default': 0},
    'LuminanceAdjustmentAqua': {
        'type': int, 'values': [-100, 100], 'default': 0},
    'LuminanceAdjustmentBlue': {
        'type': int, 'values': [-100, 100], 'default': 0},
    'LuminanceAdjustmentGreen': {
        'type': int, 'values': [-100, 100], 'default': 0},
    'LuminanceAdjustmentMagenta': {
        'type': int, 'values': [-100, 100], 'default': 0},
    'LuminanceAdjustmentOrange': {
        'type': int, 'values': [-100, 100], 'default': 0},
    'LuminanceAdjustmentPurple': {
        'type': int, 'values': [-100, 100], 'default': 0},
    'LuminanceAdjustmentRed': {
        'type': int, 'values': [-100, 100], 'default': 0},
    'LuminanceAdjustmentYellow': {
        'type': int, 'values': [-100, 100], 'default': 0},
    'ParametricDarks': {
        'type': int, 'values': [-100, 100], 'default': 0, 'plus': True},
    'ParametricHighlightSplit': {
        'type': int, 'values': [-100, 100], 'default': 75},
    'ParametricHighlights': {
        'type': int, 'values': [-100, 100], 'default': 0, 'plus': True},
    'ParametricLights': {
        'type': int, 'values': [-100, 100], 'default': 0, 'plus': True},
    'ParametricMidtoneSplit': {
        'type': int, 'values': [-100, 100], 'default': 50},
    'ParametricShadowSplit': {
        'type': int, 'values': [-100, 100], 'default': 25},
    'ParametricShadows': {
        'type': int, 'values': [-100, 100], 'default': 0, 'plus': True},
    'PerspectiveHorizontal': {'type': int, 'values': [-100, 100], 'default': 0},
    'PerspectiveRotate': {'type': int, 'values': [-100, 100], 'default': 0},
    'PerspectiveScale': {'type': int, 'values': [-100, 100], 'default': 100},
    'PerspectiveVertical': {'type': int, 'values': [-100, 100], 'default': 0},
    'PostCropVignetteAmount': {'type': int, 'values': [-100, 100], 'default': 0},
    'ProcessVersion': {'type': int, 'values': [-100, 100], 'default': 0},
    'SaturationAdjustmentAqua': {'type': int, 'values': [-100, 100], 'default': 0},
    'SaturationAdjustmentBlue': {'type': int, 'values': [-100, 100], 'default': 0},
    'SaturationAdjustmentGreen': {'type': int, 'values': [-100, 100], 'default': 0},
    'SaturationAdjustmentMagenta': {'type': int, 'values': [-100, 100], 'default': 0},
    'SaturationAdjustmentOrange': {'type': int, 'values': [-100, 100], 'default': 0},
    'SaturationAdjustmentPurple': {'type': int, 'values': [-100, 100], 'default': 0},
    'SaturationAdjustmentRed': {'type': int, 'values': [-100, 100], 'default': 0},
    'SaturationAdjustmentYellow': {'type': int, 'values': [-100, 100], 'default': 0},
    'SharpenDetail': {'type': int, 'values': [-100, 100], 'default': 0},
    'SharpenEdgeMasking': {'type': int, 'values': [-100, 100], 'default': 0},
    'SharpenRadius': {
        'type': float, 'values': [-100, 100], 'default': 0, 'plus': True},
    'SplitToningBalance': {'type': int, 'values': [-100, 100], 'default': 0},
    'SplitToningHighlightHue': {'type': int, 'values': [-100, 100], 'default': 0},
    'SplitToningHighlightSaturation': {'type': int, 'values': [-100, 100], 'default': 0},
    'SplitToningShadowHue': {'type': int, 'values': [-100, 100], 'default': 0},
    'SplitToningShadowSaturation': {'type': int, 'values': [-100, 100], 'default': 0},
    'Vibrance': {
        'type': int,
        'values': [-100, 100],
        'default': 0,
        'plus': True,
    },
}

DEPRECATED = {
    'Exposure': {'type': float, 'values': [-4.0, 4.0], 'default': 0},
    'Contrast': {'type': int, 'values': [-100, 100], 'default': 0},
    'Shadows': {'type': int, 'values': [-100, 100], 'default': 0},
    # skipping Tonecurve
    'ToneCurveName': { 'type': str, 'values': ['Linear'], 'default': 'Linear'},
}

CRS_2012 = {
    'Blacks2012': {
        'type': int, 'values': [-100, 100], 'default': 0, 'plus': True},
    'Clarity2012': {
        'type': int, 'values': [-100, 100], 'default': 0, 'plus': True},
    'Contrast2012': {
        'type': int, 'values': [-100, 100], 'default': 0, 'plus': True},
    'Exposure2012': {
        'type': float, 'values': [-8.0, 5.0], 'default': 0, 'plus': True},
    'Highlights2012': {
        'type': int, 'values': [-100, 100], 'default': 0, 'plus': True},
    'Shadows2012': {
        'type': int, 'values': [-100, 100], 'default': 0, 'plus': True},
    'Whites2012': {
        'type': int, 'values': [-100, 100], 'default': 0, 'plus': True},
    'ToneCurveName2012': {
        'type': str, 'values': ['Linear'], 'default': 'Linear'},
}
REAL_CRS = {
    'AutoBrightness': {'type': bool, 'values': [False, True], 'default': False},
    'AutoContrast': {'type': bool, 'values': [False, True], 'default': False},
    'AutoExposure': {'type': bool, 'values': [False, True], 'default': False},
    'AutoShadows': {'type': bool, 'values': [False, True], 'default': False},
    'BlueHue': {'type': int, 'values': [-100, 100], 'default': 0},
    'BlueSaturation': {'type': int, 'values': [-100, 100], 'default': 0},
    'Brightness': {'type': int, 'values': [0, 150], 'default': 0},
    'CameraProfile': {
        'type': str,
        'values': ['Adobe Standard'],
        'default': 'Adobe Standard',
    },
    'ChromaticAberrationB': {'type': int, 'values': [-100, 100], 'default': 0},
    'ChromaticAberrationR': {'type': int, 'values': [-100, 100], 'default': 0},
    'ColorNoiseReduction': {'type': int, 'values': [0, 100], 'default': 0},
    'CropAngle': {'type': float, 'values': [0, 1], 'default': 0},
    'CropBottom': {'type': float, 'values': [0, 1], 'default': 1},
    'CropLeft': {'type': float, 'values': [0, 1], 'default': 0},
    'CropRight': {'type': float, 'values': [0, 1], 'default': 1},
    'CropTop': {'type': float, 'values': [0, 1], 'default': 0},
    'CropHeight': {'type': float, 'values': [0, 1], 'default': 0},
    'CropWidth': {'type': float, 'values': [0, 1], 'default': 0},
    'CropUnits': {'type': int, 'values': [-100, 100], 'default': 0},
    'GreenHue': {'type': int, 'values': [-100, 100], 'default': 0},
    'GreenSaturation': {'type': int, 'values': [-100, 100], 'default': 0},
    'HasCrop': {'type': bool, 'values': [False, True], 'default': False},
    'HasSetting1s': {
        'type': bool,
        'values': [False, True],
        'default': True
    },
    'LuminanceSmoothing': {'type': int, 'values': [0, 100], 'default': 0},
    'RawFileName': {'type': str, 'values': None, 'default': None},
    'RedHue': {'type': int, 'values': [-100, 100], 'default': 0},
    'RedSaturation': {'type': int, 'values': [-100, 100], 'default': 0},
    'Saturation': {
        'type': int,
        'values': [-100, 100],
        'default': 0,
        'plus': True,
    },
    'ShadowTint': {'type': int, 'values': [-100, 100], 'default': 0},
    'Sharpness': {'type': int, 'values': [-100, 100], 'default': 0},
    'Temperature': {'type': int, 'values': [2000, 50000], 'default': 5200},
    'Tint': {'type': int, 'values': [-150, 150], 'default': 0, 'plus': True},
    'Version': {
        'type': str, 'values': ['7.4'], 'default': '7.4'},
    'VignetteAmount': {'type': int, 'values': [-100, 100], 'default': 0},
    'VignetteMidpoint': {
        'type': int, 'values': [0, 100], 'default': 0},
    'WhiteBalance': {
        'type': str,
        'values': [
            'As Shot', 'Daylight', 'Cloudy', 'Shade', 'Tungsten',
            'Flourescent', 'Flash', 'Custom'
        ],
        'default': 'As Shot',
    },
}
ALL_CRS = dict(CRS.items() + REAL_CRS.items() + CRS_2012.items())
CROP_MAPPINGS = {
    False: False,
    True: True,
    0: False,
    1: True,
    'No': False,
    'Yes': True,
}
MAPPINGS = {
    'CropAngle': set(['CanonVRD:AngleAdj',]),
    'CropLeft': set(['CanonVRD:CropLeft']),
    'CropTop': set(['CanonVRD:CropTop']),
    'CropRight': set(['CanonVRD:CropWidth']),
    'CropBottom': set(['CanonVRD:CropHeight']),
    'CropWidth': set(['CanonVRD:CropWidth']),
    'CropHeight': set(['CanonVRD:CropHeight']),
    'HasCrop': set(['CanonVRD:CropActive',]),
    'Saturation': set(['CanonVRD:RawSaturation']),
    'Sharpness': set([
        'CanonVRD:RawSharpness',
        'CanonVRD:SharpnessAdj',
        'MakerNotes:Sharpness',
    ]),
    'Temperature': set([
        'CanonVRD:WBAdjColorTemp',
        'MakerNotes:ColorTemperature',
    ]),
    'WhiteBalance': set([
        # this is manually mapped if the vrd exists
        'CanonVRD:WhiteBalanceAdj',
        'EXIF:WhiteBalance',
        'MakerNotes:WhiteBalance',
    ]),
    'Contrast2012': set([
        'CanonVRD:ContrastAdj',
        'CanonVRD:RawContrast',
        'MakerNotes:Contrast',
    ]),
    'Exposure2012': set([
        'CanonVRD:RawBrightnessAdj',
        'CanonVRD:BrightnessAdj',
    ]),
    'Highlights2012': set([
        'CanonVRD:RawHighlight',
    ]),
    'Shadows2012': set([
        'CanonVRD:RawShadow',
    ]),
    'ImageHeight': set([
        'tiff:ImageHeight',
        'exif:PixelYDimension',
        'MakerNotes:CanonImageHeight',
        'EXIF:ExifImageHeight',
    ]),
    'ImageWidth': set([
        'tiff:ImageWidth',
        'exif:PixelXDimension',
        'MakerNotes:CanonImageWidth',
        'EXIF:ExifImageWidth',
    ]),
}
LIKELY_MAPPINGS = {}

def process_metadata(metadata):
    picture_style = metadata.get('CanonVRD:PictureStyle')
    if picture_style:
        if picture_style in PICTURE_STYLES:
            picture_style = PICTURE_STYLES[picture_style]
            picture_key = 'CanonVRD:' + picture_style
            for key, setting in metadata.items():
                if key.startswith(picture_key):
                    new_key = key.replace(picture_key, 'CanonVRD:')
                    metadata[new_key] = metadata[key]
    for mapping, sources in MAPPINGS.items():
        found = False
        for source in sources:
            if found:
                continue
            if source in metadata:
                metadata['crs:' + mapping] = metadata[source]
                found = True
        if not found:
            print 'Not found: {} {}'.format(mapping, sources)

    if 'CanonVRD:WhiteBalanceAdj' in metadata:
        metadata['crs:WhiteBalance'] = WHITE_BALANCE_MAPPINGS[
            metadata['CanonVRD:WhiteBalanceAdj']]
    metadata['crs:HasCrop'] = CROP_MAPPINGS[
        metadata.get('CanonVRD:CropActive', False)]
    height = metadata['crs:ImageHeight']
    width = metadata['crs:ImageWidth']
    orientation = metadata.get('tiff:Orientation', 'Horizontal (normal)')
    if metadata['crs:HasCrop']:
        croptop = metadata.get('CanonVRD:CropTop', 0)
        cropheight = metadata.get('CanonVRD:CropHeight', height)
        cropleft = metadata.get('CanonVRD:CropLeft', 0)
        cropwidth = metadata.get('CanonVRD:CropWidth', width)
        degrees = metadata.get('CanonCRD:AngleAdj')
        image = Image(height, width, orientation)
        image.crop(croptop, cropleft, cropheight, cropwidth, degrees)
        t, l, b, r = image.getXMPCrop()
        metadata['crs:CropTop'] = round(t, 6)
        metadata['crs:CropLeft'] = round(l, 6)
        metadata['crs:CropBottom'] = round(b, 6)
        metadata['crs:CropRight'] = round(r, 6)
    return metadata

def format_field(k, v):
    if k not in ALL_CRS:
        return str(v)
    f = ALL_CRS[k]['type']
    v = f(v)
    if f == bool:
        if v:
            return 'True'
        else:
            return False
    if ALL_CRS[k].get('plus') and v > 0:
        return '+{}'.format(v)
    return v

def metadata_to_fields(metadata):
    lines = []
    whitelist = [
        'xmp', 'tiff', 'exif', 'dc', 'aux', 'photoshop', 'xmpMM', 'stEvt', 'crs'
    ]
    for k, v in metadata.items():
        if ':' not in k:
            continue
        group, w = k.split(':')
        if group.lower() in whitelist:
            group = group.lower()
            k = '{}:{}'.format(group, w)
        if group in whitelist:
            lines.append('{}="{}"'.format(k, format_field(k, v)))
    for k, definition in ALL_CRS.items():
        k = 'crs:' + k
        if k in metadata:
            continue
        else:
            lines.append('{}="{}"'.format(
                k, format_field(k, definition['default'])))
    lines = sorted(lines)
    fields = "\r\n   ".join(lines)
    return fields

def main(fileglobs):
    import os
    template = open(os.path.dirname(os.path.abspath(__file__))
                    + '/template.xmp').read()
    with exiftool.ExifTool() as et:
        for fileglob in fileglobs:
            files = [x for x in glob.glob(fileglob) if x.endswith('.cr2')]
            if not files:
                print 'No files for glob %s' % fileglob
                continue
            for i, filename in enumerate(files):
                xmp_filename = filename[0:-3] + 'xmp'
                replace_xmp = True
                if os.path.exists(xmp_filename):
                    cr2_mtime = os.path.getmtime(filename)
                    xmp_mtime = os.path.getmtime(xmp_filename)
                    replace_xmp = cr2_mtime > xmp_mtime
                if replace_xmp:
                    metadata = et.get_metadata(filename)
                    metadata = process_metadata(metadata)
                    output = template.replace(
                        '##FIELDS##',
                        metadata_to_fields(metadata)
                    )
                    f = open(xmp_filename, 'w')
                    f.write(output)
                    f.close()

if __name__ == '__main__':
    import sys
    fileglobs = sys.argv[1:]
    if not fileglobs:
        print 'No files specified'
        exit(1)
    main(fileglobs)
