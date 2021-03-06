import bpy
from bpy.props import *
from mathutils import *
from .common import *

class YDeselectAction(bpy.types.Operator):
    bl_idname = "armature.y_deselect_action"
    bl_label = "Deselect Action"
    bl_description = "Deselect action"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = get_current_armature_object()
        return obj and obj.animation_data

    def execute(self, context):
        obj = get_current_armature_object()
        obj.animation_data.action = None

        for pb in obj.pose.bones:
            #Set the rotation to 0
            pb.rotation_quaternion = Quaternion((0, 0, 0), 0)
            #Set the scale to 1
            pb.scale = Vector((1, 1, 1))
            #Set the location at rest (edit) pose bone position
            pb.location = Vector((0, 0, 0))

        return {'FINISHED'}

class YRigifyExportActionPanel(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    #bl_context = "objectmode"
    bl_label = "Action Manager"
    bl_category = "UE4 Helper"

    @classmethod
    def poll(cls, context):
        return get_current_armature_object()

    def draw(self, context):
        obj = get_current_armature_object()

        scene_props = context.scene.rigify_export_props
        props = context.window_manager.rigify_export_props

        col = self.layout.column()

        action = None

        # Check active action
        if obj.animation_data:
            action = obj.animation_data.action
            if action and action != bpy.data.actions[props.active_action]:
                index = [i for i,a in enumerate(bpy.data.actions) if a == action][0]
                props.active_action = index

        col.template_list("ACTION_UL_y_action_lists", "", bpy.data,
                "actions", props, "active_action", rows=3, maxrows=5)  

        if action:
            col.operator('armature.y_deselect_action', icon='ACTION')

        col.prop(scene_props, 'sync_frames')
        col.prop(scene_props, 'sync_bone_layers')

class ACTION_UL_y_action_lists(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        action_props = item.rigify_export_props
        row = layout.row(align=True)
        row.prop(item, 'name', text='', emboss=False, icon='ACTION')

        if action_props.enable_loop:
            rrow = row.row(align=True)
            rrow.active = action_props.enable_skip_last_frame
            rrow.prop(action_props, 'enable_skip_last_frame', text='', emboss=False, icon='FRAME_PREV')

        rrow = row.row(align=True)
        rrow.active = action_props.enable_loop
        rrow.prop(action_props, 'enable_loop', text='', emboss=False, icon='FILE_REFRESH')

        rrow = row.row(align=True)
        rrow.prop(action_props, 'enable_export', text='')

def update_frame_range(self, context):
    obj =  get_current_armature_object()
    scene = context.scene
    scene_props = scene.rigify_export_props
    wm_props = context.window_manager.rigify_export_props

    if not scene_props.sync_frames: return

    # Get action
    action = bpy.data.actions[wm_props.active_action]
    action_props = action.rigify_export_props

    if obj.animation_data.action == action:
        # Set start and end frame
        scene.frame_start = action.frame_range[0]
        scene.frame_end = action.frame_range[1]

        # Skip last frame option
        if action_props.enable_loop and action_props.enable_skip_last_frame:
            scene.frame_end = scene.frame_end-1

def update_action(self, context):
    obj =  get_current_armature_object()
    scene_props = context.scene.rigify_export_props

    # Get action
    action = bpy.data.actions[self.active_action]
    action_props = action.rigify_export_props

    # Set action
    if not obj.animation_data:
        obj.animation_data_create()
    obj.animation_data.action = action

    # Update scene frame range
    update_frame_range(action, context)

    if scene_props.sync_bone_layers:

        # Get all bone names related to action
        bone_names = []
        for fcurve in action.fcurves:
            if fcurve.group and fcurve.group.name not in bone_names:
                bone_names.append(fcurve.group.name)

        # Get relevant layers
        layers = []
        for name in bone_names:
            bone = obj.data.bones.get(name)
            if bone:
                for i in range(32):
                    if bone.layers[i] and i not in layers:
                        layers.append(i)

        # Enable only relevant layers
        if layers:
            for i in range(32):
                obj.data.layers[i] = i in layers

        #print(bone_names)

class YSceneRigifyExportActionProps(bpy.types.PropertyGroup):
    sync_bone_layers = BoolProperty(
            name = 'Sync Bone Layers',
            description = 'Sync bone layers when active action changes',
            default = False
            )

    sync_frames = BoolProperty(
            name = 'Sync Frames',
            description = 'Sync frame start and end when active action changes',
            default = False
            )

class YWMRigifyExportActionProps(bpy.types.PropertyGroup):
    active_action = IntProperty(default=0, update=update_action)

class YActionRigifyExportActionProps(bpy.types.PropertyGroup):

    enable_export = BoolProperty(
            name = 'Enable Export',
            description = 'Export this action (only works on Godot for now)',
            default = True
            )

    enable_loop = BoolProperty(
            name = 'Enable Loop',
            description = 'Enable animation loop (only works on Godot for now)',
            default = False,
            update=update_frame_range)

    enable_skip_last_frame = BoolProperty(
            name = 'Enable Skip',
            description = 'Enable skip the last frame (only works on Godot for now)',
            default = True,
            update=update_frame_range)

def register():
    bpy.utils.register_class(YDeselectAction)
    bpy.utils.register_class(YRigifyExportActionPanel)
    bpy.utils.register_class(YSceneRigifyExportActionProps)
    bpy.utils.register_class(YWMRigifyExportActionProps)
    bpy.utils.register_class(YActionRigifyExportActionProps)
    bpy.utils.register_class(ACTION_UL_y_action_lists)

    bpy.types.Scene.rigify_export_props = PointerProperty(type=YSceneRigifyExportActionProps)
    bpy.types.Action.rigify_export_props = PointerProperty(type=YActionRigifyExportActionProps)
    bpy.types.WindowManager.rigify_export_props = PointerProperty(type=YWMRigifyExportActionProps)

def unregister():
    bpy.utils.unregister_class(YDeselectAction)
    bpy.utils.unregister_class(YRigifyExportActionPanel)
    bpy.utils.unregister_class(YSceneRigifyExportActionProps)
    bpy.utils.unregister_class(YWMRigifyExportActionProps)
    bpy.utils.unregister_class(YActionRigifyExportActionProps)
    bpy.utils.unregister_class(ACTION_UL_y_action_lists)
