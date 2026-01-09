import maya.api.OpenMaya as om
import maya.api.OpenMayaAnim as oma


class MotionTrailCurve(om.MPxNode):
    '''Motion Trail Curve'''

    id = om.MTypeId(0x00121EC9)
    back_time = om.MObject()
    step = om.MObject()
    matrix_in = om.MObject()
    output_curve = om.MObject()

    @staticmethod
    def creator() -> om.MPxNode:
        '''Return my instance.'''
        return MotionTrailCurve()

    @staticmethod
    def initialize() -> None:
        '''Initialize plug-ins.'''
        nAttr = om.MFnNumericAttribute()
        MotionTrailCurve.back_time = nAttr.create(
            'backTime', 'bt', om.MFnNumericData.kFloat, 10.0
        )
        nAttr.storable = True
        nAttr.writable = True
        nAttr.setMin(0.001)
        nAttr.setSoftMin(nAttr.getMin())

        nAttr = om.MFnNumericAttribute()
        MotionTrailCurve.step = nAttr.create(
            'step', 'st', om.MFnNumericData.kFloat, 1.0
        )
        nAttr.storable = True
        nAttr.writable = True
        nAttr.setMin(0.001)
        nAttr.setSoftMin(nAttr.getMin())

        mAttr = om.MFnMatrixAttribute()
        MotionTrailCurve.matrix_in = mAttr.create('matrixIn', 'matrixIn')

        tAttr = om.MFnTypedAttribute()
        MotionTrailCurve.output_curve = tAttr.create(
            'outputCurve',
            'oc',
            om.MFnNurbsCurveData.kNurbsCurve,
            om.MObject.kNullObj,
        )
        tAttr.readable = True
        tAttr.writable = False
        tAttr.storable = False

        MotionTrailCurve.addAttribute(MotionTrailCurve.back_time)
        MotionTrailCurve.addAttribute(MotionTrailCurve.step)
        MotionTrailCurve.addAttribute(MotionTrailCurve.matrix_in)
        MotionTrailCurve.addAttribute(MotionTrailCurve.output_curve)

        MotionTrailCurve.attributeAffects(
            MotionTrailCurve.back_time, MotionTrailCurve.output_curve
        )
        MotionTrailCurve.attributeAffects(
            MotionTrailCurve.step, MotionTrailCurve.output_curve
        )
        MotionTrailCurve.attributeAffects(
            MotionTrailCurve.matrix_in, MotionTrailCurve.output_curve
        )

    def __init__(self) -> None:
        '''Initilize instance.'''
        om.MPxNode.__init__(self)

    def compute(self, plug: om.MPlug, dataBlock: om.MDataBlock) -> None:
        '''Compute curve points.'''
        if plug == MotionTrailCurve.output_curve:
            back_time = dataBlock.inputValue(
                MotionTrailCurve.back_time
            ).asFloat()
            step = dataBlock.inputValue(MotionTrailCurve.step).asFloat()
            if back_time - step <= 0.0:
                return

            matrix_in_plug = om.MPlug(
                self.thisMObject(), MotionTrailCurve.matrix_in
            )
            fps = om.MTime.uiUnit()
            current_time = oma.MAnimControl.currentTime().asUnits(fps)

            points = om.MPointArray()
            knots = om.MDoubleArray()
            for i, _time in enumerate(
                frange(current_time, current_time - back_time, step * -1)
            ):
                matrix_object = matrix_in_plug.asMObject(
                    om.MDGContext(om.MTime(_time, fps))
                )
                pos = (
                    om.MFnMatrixData(matrix_object)
                    .transformation()
                    .translation(om.MSpace.kWorld)
                )
                points.append(pos)
                knots.append(float(i))

            curve_data = om.MFnNurbsCurveData().create()
            curve_fn = om.MFnNurbsCurve()
            curve_fn.create(
                points,
                knots,
                1,
                om.MFnNurbsCurve.kOpen,
                False,
                False,
                curve_data,
            )
            output_handle = dataBlock.outputValue(MotionTrailCurve.output_curve)
            output_handle.setMObject(curve_data)
            dataBlock.setClean(plug)


def frange(start: float, end: float, step: float) -> list[float]:
    if step == 0:
        raise ValueError('step must not be zero')

    start = start
    end = end
    step = step
    if abs(step) >= abs(start - end):
        return [start]

    exp = len(str(step).split('.')[1])
    start = int(start * 10**exp)
    end = int(end * 10**exp)
    step = int(step * 10**exp)

    result = [round(val * 10**-exp, exp) for val in range(start, end, step)]
    return result


def maya_useNewAPI() -> None:
    '''Send to Maya to use OpenMaya 2.0.'''


def initializePlugin(obj: om.MObject) -> None:
    '''Registering plug-ins to Maya.'''
    mplugin = om.MFnPlugin(obj, '@takkun3d', '1.00')
    try:
        mplugin.registerNode(
            'motionTrailCurve',
            MotionTrailCurve.id,
            MotionTrailCurve.creator,
            MotionTrailCurve.initialize,
            om.MPxNode.kDependNode,
        )
    except:
        om.MGlobal.displayError('Faled to register node: MotionTrailCurve')
        raise


def uninitializePlugin(obj: om.MObject) -> None:
    '''Unload plug-ins from Maya.'''
    mplugin = om.MFnPlugin(obj)
    try:
        mplugin.deregisterNode(MotionTrailCurve.id)
    except:
        om.MGlobal.displayError('Faled to uninitialize node: MotionTrailCurve')
        raise
