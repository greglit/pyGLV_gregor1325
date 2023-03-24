import numpy as np

import pyECSS.utilities as util
from pyECSS.Entity import Entity
from pyECSS.Component import BasicTransform, Camera, RenderMesh
from pyECSS.System import  TransformSystem, CameraSystem
from pyGLV.GL.Scene import Scene
from pyGLV.GUI.Viewer import RenderGLStateSystem

from pyGLV.GL.Shader import InitGLShaderSystem, Shader, ShaderGLDecorator, RenderGLShaderSystem
from pyGLV.GL.VertexArray import VertexArray

from OpenGL.GL import GL_LINES


scene = Scene()    

# Scenegraph with Entities, Components
rootEntity = scene.world.createEntity(Entity(name="RooT"))
entityCam1 = scene.world.createEntity(Entity(name="entityCam1"))
scene.world.addEntityChild(rootEntity, entityCam1)
trans1 = scene.world.addComponent(entityCam1, BasicTransform(name="trans1", trs=util.identity()))

entityCam2 = scene.world.createEntity(Entity(name="entityCam2"))
scene.world.addEntityChild(entityCam1, entityCam2)
trans2 = scene.world.addComponent(entityCam2, BasicTransform(name="trans2", trs=util.identity()))
# orthoCam = scene.world.addComponent(entityCam2, Camera(util.ortho(-100.0, 100.0, -100.0, 100.0, 1.0, 100.0), "orthoCam","Camera","500"))

node4 = scene.world.createEntity(Entity(name="node4"))
scene.world.addEntityChild(rootEntity, node4)
trans4 = scene.world.addComponent(node4, BasicTransform(name="trans4", trs=util.translate(0,0.5,0))) #util.identity()
mesh4 = scene.world.addComponent(node4, RenderMesh(name="mesh4"))






## GENEARTE PLOT DATA ##

plot = scene.world.createEntity(Entity(name="plot"))
scene.world.addEntityChild(rootEntity, plot)
plot_trans = scene.world.addComponent(plot, BasicTransform(name="plot_trans", trs=util.identity()))
plot_mesh = scene.world.addComponent(plot, RenderMesh(name="plot_mesh"))

def plot_function(x):
    return x**2
    #return x + x**2 + 2*x**3 + 0.5*x**4

def generate_plot_function_data(plot_function, numberPoints, start_x_coord, end_x_coord):
    verticies = np.empty((0, 4), np.float32)
    colors = np.empty((0, 4), np.float32)
    indecies = np.array(range((numberPoints*2)-2), np.uint32)
    span = abs(start_x_coord-end_x_coord)
    #np.linspace()
    #print("span", span)
    for i in range(numberPoints):
        x_coord = start_x_coord+(i*(span/numberPoints))
        #print("x_coord", x_coord)
        y_coord = plot_function(x_coord)
        new_vertex = [x_coord, y_coord, 0.0, 1.0]
        verticies = np.append(verticies, [new_vertex, new_vertex], axis=0)
        colors = np.append(colors, [[1.0, 0.0, 0.0, 1.0],[1.0, 0.0, 0.0, 1.0]], axis=0)
    verticies = verticies[1:-1]
    colors = colors[1:-1]
    return verticies, colors, indecies

verticies, colors, indecies = generate_plot_function_data(plot_function, 100, -5, 5)
#print("plot_data", verticies, colors, indecies)


## ADD PLOT ##
plot = scene.world.createEntity(Entity(name="plot"))
scene.world.addEntityChild(rootEntity, plot)
plot_trans = scene.world.addComponent(plot, BasicTransform(name="plot_trans", trs=util.identity()))
plot_mesh = scene.world.addComponent(plot, RenderMesh(name="plot_mesh"))
plot_mesh.vertex_attributes.append(verticies) 
plot_mesh.vertex_attributes.append(colors)
plot_mesh.vertex_index.append(indecies)
scene.world.addComponent(plot, VertexArray(primitive=GL_LINES)) # note the primitive change

axes_shader = scene.world.addComponent(plot, ShaderGLDecorator(Shader(vertex_source = Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG)))








# Systems
transUpdate = scene.world.createSystem(TransformSystem("transUpdate", "TransformSystem", "001"))
# camUpdate = scene.world.createSystem(CameraSystem("camUpdate", "CameraUpdate", "200"))
renderUpdate = scene.world.createSystem(RenderGLShaderSystem())
initUpdate = scene.world.createSystem(InitGLShaderSystem())


vArray4 = scene.world.addComponent(node4, VertexArray())
shaderDec4 = scene.world.addComponent(node4, ShaderGLDecorator(Shader(vertex_source = Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG)))


# Generate terrain
from pyGLV.GL.terrain import generateTerrain
vertexTerrain, indexTerrain, colorTerrain= generateTerrain(size=4,N=20)
# Add terrain
terrain = scene.world.createEntity(Entity(name="terrain"))
scene.world.addEntityChild(rootEntity, terrain)
terrain_trans = scene.world.addComponent(terrain, BasicTransform(name="terrain_trans", trs=util.identity()))
terrain_mesh = scene.world.addComponent(terrain, RenderMesh(name="terrain_mesh"))
terrain_mesh.vertex_attributes.append(vertexTerrain) 
terrain_mesh.vertex_attributes.append(colorTerrain)
terrain_mesh.vertex_index.append(indexTerrain)
terrain_vArray = scene.world.addComponent(terrain, VertexArray(primitive=GL_LINES))
terrain_shader = scene.world.addComponent(terrain, ShaderGLDecorator(Shader(vertex_source = Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG)))
# terrain_shader.setUniformVariable(key='modelViewProj', value=mvpMat, mat4=True)


# MAIN RENDERING LOOP

running = True
scene.init(imgui=True, windowWidth = 1024, windowHeight = 768, windowTitle = "Elements: A Working Event Manager", openGLversion = 4)

# pre-pass scenegraph to initialise all GL context dependent geometry, shader classes
# needs an active GL context
scene.world.traverse_visit(initUpdate, scene.world.root)

################### EVENT MANAGER ###################

eManager = scene.world.eventManager
gWindow = scene.renderWindow
gGUI = scene.gContext

renderGLEventActuator = RenderGLStateSystem()


eManager._subscribers['OnUpdateWireframe'] = gWindow
eManager._actuators['OnUpdateWireframe'] = renderGLEventActuator
eManager._subscribers['OnUpdateCamera'] = gWindow 
eManager._actuators['OnUpdateCamera'] = renderGLEventActuator
# MANOS END
# Add RenderWindow to the EventManager publishers
# eManager._publishers[updateBackground.name] = gGUI


eye = util.vec(2.5, 2.5, 2.5)
target = util.vec(0.0, 0.0, 0.0)
up = util.vec(0.0, 1.0, 0.0)
view = util.lookat(eye, target, up)
# projMat = util.ortho(-10.0, 10.0, -10.0, 10.0, -1.0, 10.0) ## WORKING
# projMat = util.perspective(90.0, 1.33, 0.1, 100) ## WORKING
projMat = util.perspective(50.0, 1.0, 0.01, 10.0) ## WORKING 

gWindow._myCamera = view # otherwise, an imgui slider must be moved to properly update


model_cube = trans4.trs
# OR
# model_cube = util.scale(0.3) @ util.translate(0.0,0.5,0.0) ## COMPLETELY OVERRIDE OBJECT's TRS
# OR
# model_cube =  trans4.trs @ util.scale(0.3) @ util.translate(0.0,0.5,0.0) ## TAMPER WITH OBJECT's TRS

model_terrain_axes = terrain.getChild(0).trs # notice that terrain.getChild(0) == terrain_trans
# OR 
# model_terrain_axes = util.translate(0.0,0.0,0.0) ## COMPLETELY OVERRIDE OBJECT's TRS

while running:
    running = scene.render(running)
    scene.world.traverse_visit(renderUpdate, scene.world.root)
    view =  gWindow._myCamera # updates view via the imgui
    mvp_cube = projMat @ view @ model_cube
    mvp_terrain_axes = projMat @ view @ model_terrain_axes
    axes_shader.setUniformVariable(key='modelViewProj', value=mvp_terrain_axes, mat4=True)
    terrain_shader.setUniformVariable(key='modelViewProj', value=mvp_terrain_axes, mat4=True)
    shaderDec4.setUniformVariable(key='modelViewProj', value=mvp_cube, mat4=True)
    scene.render_post()
    
scene.shutdown()



