import os.path
import pkgutil
import OpenGL.GL as gl


from .gl_rendering import Program, Technique


# TODO: pkgutils way
TEXTURES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            os.path.pardir,
                            'textures')


EGA_TECHNIQUE = Technique(Program(pkgutil.get_data('poolvr', 'shaders/ega_vs.glsl').decode(),
                                  pkgutil.get_data('poolvr', 'shaders/ega_fs.glsl').decode()),
                          uniforms={'u_color': {'value': [1.0, 0.0, 0.0, 0.0]}})


LAMBERT_TECHNIQUE = Technique(Program(pkgutil.get_data('poolvr', 'shaders/lambert_vs.glsl').decode(),
                                      pkgutil.get_data('poolvr', 'shaders/lambert_fs.glsl').decode()),
                              uniforms={'u_color': {'value': [0.0, 1.0, 1.0, 0.0]},
                                        'u_lightpos': {'value': [1.0, 15.0, 1.5]}})


SKYBOX_TECHNIQUE = Technique(Program(pkgutil.get_data('poolvr', 'shaders/skybox_vs.glsl').decode(),
                                     pkgutil.get_data('poolvr', 'shaders/skybox_fs.glsl').decode()),
                             attributes={'a_position': {'type': gl.GL_FLOAT_VEC3}},
                             uniforms={'u_modelview': {'type': gl.GL_FLOAT_MAT4},
                                       'u_projection': {'type': gl.GL_FLOAT_MAT4},
                                       'u_map': {'type': gl.GL_SAMPLER_CUBE}},
                             front_face=gl.GL_CW)