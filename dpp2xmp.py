import exiftool
import glob
import pprint
import re

# http://www.exiv2.org/tags-xmp-crs.html
# http://wwwimages.adobe.com/www.adobe.com/content/dam/Adobe/en/devnet/xmp/pdfs/cs6/XMPSpecificationPart2.pdf
# http://www.sno.phy.queensu.ca/~phil/exiftool/TagNames/CanonVRD.html
# http://www.adobe.com/content/dam/Adobe/en/devnet/xmp/pdfs/XMPSpecificationPart1.pdf


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
    'CameraProfileDigest': {'type': int, 'values': [-100, 100], 'default': 0},
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
    'LensProfileDistortionScale': {'type': int, 'values': [-100, 100], 'default': 0},
    'LensProfileEnable': {'type': int, 'values': [-100, 100], 'default': 0},
    'LensProfileFilename': {'type': int, 'values': [-100, 100], 'default': 0},
    'LensProfileName': {'type': int, 'values': [-100, 100], 'default': 0},
    'LensProfileSetup': {'type': int, 'values': [-100, 100], 'default': 0},
    'LensProfileVignettingScale': {'type': int, 'values': [-100, 100], 'default': 0},
    'LuminanceAdjustmentAqua': {'type': int, 'values': [-100, 100], 'default': 0},
    'LuminanceAdjustmentBlue': {'type': int, 'values': [-100, 100], 'default': 0},
    'LuminanceAdjustmentGreen': {'type': int, 'values': [-100, 100], 'default': 0},
    'LuminanceAdjustmentMagenta': {'type': int, 'values': [-100, 100], 'default': 0},
    'LuminanceAdjustmentOrange': {'type': int, 'values': [-100, 100], 'default': 0},
    'LuminanceAdjustmentPurple': {'type': int, 'values': [-100, 100], 'default': 0},
    'LuminanceAdjustmentRed': {'type': int, 'values': [-100, 100], 'default': 0},
    'LuminanceAdjustmentYellow': {'type': int, 'values': [-100, 100], 'default': 0},
    'ParametricDarks': {'type': int, 'values': [-100, 100], 'default': 0},
    'ParametricHighlightSplit': {'type': int, 'values': [-100, 100], 'default': 75},
    'ParametricHighlights': {'type': int, 'values': [-100, 100], 'default': 0},
    'ParametricLights': {'type': int, 'values': [-100, 100], 'default': 0},
    'ParametricMidtoneSplit': {'type': int, 'values': [-100, 100], 'default': 50},
    'ParametricShadowSplit': {'type': int, 'values': [-100, 100], 'default': 25},
    'ParametricShadows': {'type': int, 'values': [-100, 100], 'default': 0},
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
    'SharpenRadius': {'type': int, 'values': [-100, 100], 'default': 0},
    'SplitToningBalance': {'type': int, 'values': [-100, 100], 'default': 0},
    'SplitToningHighlightHue': {'type': int, 'values': [-100, 100], 'default': 0},
    'SplitToningHighlightSaturation': {'type': int, 'values': [-100, 100], 'default': 0},
    'SplitToningShadowHue': {'type': int, 'values': [-100, 100], 'default': 0},
    'SplitToningShadowSaturation': {'type': int, 'values': [-100, 100], 'default': 0},
    'Vibrance': {'type': int, 'values': [-100, 100], 'default': 0},
}
REAL_CRS = {
    'BlueHue': {'type': int, 'values': [-100, 100], 'default': 0},
    'BlueSaturation': {'type': int, 'values': [-100, 100], 'default': 0},
    'CameraProfile': {
        'type': str,
        'values': ['Adobe Standard'],
        'default': 'Adobe Standard',
    },
    'ColorNoiseReduction': {'type': int, 'values': [-100, 100], 'default': 0},
    'CropAngle': {'type': float, 'values': [0, 1], 'default': 0},
    'CropBottom': {'type': float, 'values': [0, 1], 'default': 1},
    'CropLeft': {'type': float, 'values': [0, 1], 'default': 0},
    'CropRight': {'type': float, 'values': [0, 1], 'default': 1},
    'CropTop': {'type': float, 'values': [0, 1], 'default': 0},
    'GreenHue': {'type': int, 'values': [-100, 100], 'default': 0},
    'GreenSaturation': {'type': int, 'values': [-100, 100], 'default': 0},
    'HasCrop': {'type': bool, 'values': [False, True], 'default': False},
    'HasSettings': {'type': bool, 'values': [False, True], 'default': False},
    'LuminanceSmoothing': {'type': int, 'values': [0, 100], 'default': 0},
    'RawFileName': {'type': str, 'values': None, 'default': None},
    'RedHue': {'type': int, 'values': [-100, 100], 'default': 0},
    'RedSaturation': {'type': int, 'values': [-100, 100], 'default': 0},
    'Saturation': {'type': int, 'values': [-100, 100], 'default': 0},
    'ShadowTint': {'type': int, 'values': [-100, 100], 'default': 0},
    'Sharpness': {'type': int, 'values': [-100, 100], 'default': 0},
    'Temperature': {'type': int, 'values': [-100, 100], 'default': 0},
    'Tint': {'type': int, 'values': [-100, 100], 'default': 0},
    'Version': {'type': str, 'values': [-100, 100], 'default': 0},
    'VignetteAmount': {'type': int, 'values': [-100, 100], 'default': 0},
    'WhiteBalance': {
        'type': str,
        'values': [
            'As Shot', 'Daylight', 'Cloudy', 'Shade', 'Tungsten',
            'Flourescent', 'Flash', 'Custom'
        ],
        'default': 'As Shot',
    },
}

CRS_2012 = {
    'Blacks2012': {'type': int, 'values': [-100, 100], 'default': 0},
    'Clarity2012': {'type': int, 'values': [-100, 100], 'default': 0},
    'Contrast2012': {'type': int, 'values': [-100, 100], 'default': 0},
    'Exposure2012': {'type': float, 'values': [-10.0, 10.0], 'default': 0},
    'Highlights2012': {'type': int, 'values': [-100, 100], 'default': 0},
    'Shadows2012': {'type': int, 'values': [-100, 100], 'default': 0},
    'Whites2012': {'type': int, 'values': [-100, 100], 'default': 0},
    'ToneCurveName2012': {
        'type': str, 'values': ['Linear'], 'default': 'Linear'},
}
ALL_CRS = dict(CRS.items() + REAL_CRS.items() + CRS_2012.items())
CROP_MAPPINGS = {
    0: False,
    1: True,
    'No': False,
    'Yes': True,
}
MAPPINGS = {
    'CropAngle': set(['CanonVRD:AngleAdj',]),
    'CropLeft': set(['CanonVRD:CropLeft']),
    'CropRight': set(['CanonVRD:CropWidth']),
    'CropTop': set(['CanonVRD:CropTop']),
    'CropBottom': set(['CanonVRD:CropHeight']),
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

    if 'CanonVRD:WhiteBalanceAdj' in metadata:
        metadata['crs:' + 'WhiteBalance'] = WHITE_BALANCE_MAPPINGS[
            metadata['CanonVRD:WhiteBalanceAdj']]
    if 'CanonVRD:CropActive' in metadata:
        metadata['crs:' + 'HasCrop'] = CROP_MAPPINGS[
            metadata['CanonVRD:CropActive']]
    return metadata

def format_field(k, v):
    if k not in ALL_CRS:
        return str(v)
    f = ALL_CRS[k]['type']
    if f == int:
        return int(v)
    if f == float:
        return float(v)
    if f == str:
        return str(v)
    if f == bool:
        if v:
            return 'True'
        else:
            return False

def metadata_to_fields(metadata):
    lines = []
    for k, v in metadata.items():
        lines.append('{}="{}"'.format(k, format_field(k, v)))
    for k, definition in ALL_CRS.items():
        k = 'crs:' + k
        if k in metadata:
            continue
        else:
            lines.append('{}="{}"'.format(
                k, format_field(k, definition['default'])))
    lines = sorted(lines)
    fields = "\r\n    ".join(lines)
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
