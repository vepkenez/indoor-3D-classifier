import numpy as np
import math
from sklearn.preprocessing import normalize
from tqdm import tqdm

def rotyaxis(xa, za, angle):
    z = xa * math.cos(angle) - za *  math.sin(angle)
    x = xa * math.sin(angle) + za * math.cos(angle) 
    return x, z

def rotxaxis(ya, za, angle):
    
    """
    y' = y*cos q - z*sin q
    z' = y*sin q + z*cos q
    x' = x

    """

    y = ya * math.cos(angle) - za * math.sin(angle) 
    z = ya * math.sin(angle) + za *  math.cos(angle)
    
    return y, z

def rotx(verts, angle):
    out = []
    for x, y, z in verts:
        y, z = rotxaxis(y, z, angle)
        out.append([x, y, z])
    return out

def roty(verts, angle):
    out = []
    for x, y, z in verts:
        x, z = rotyaxis(x, z, angle)
        out.append([x, y, z])
    return out
    

def plane(width=10, height=10, subd=10, yrot=0, xrot=0, noise=0):

    width_half = width / 2
    height_half = height / 2

    gridX = subd
    gridY = subd

    gridX1 = gridX + 1
    gridY1 = gridY + 1

    segment_width = width / gridX
    segment_height = height / gridY

    faces = []
    vertices = []

    for iy in range(gridY1):

        y = iy * segment_height - height_half

        for ix in range(gridX1):
            x = ix * segment_width - width_half

            vertices.append( [x, - y, np.random.normal()*noise] )

    vertices = rotx(vertices, xrot)
    vertices = roty(vertices, yrot)
    for iy in range(gridY):

        for ix in range(gridX):

            a = ix + gridX1 * iy
            b = ix + gridX1 * ( iy + 1 )
            c = ( ix + 1 ) + gridX1 * ( iy + 1 )
            d = ( ix + 1 ) + gridX1 * iy

            faces.append([a, b, d])
            faces.append([b, c, d])

    return np.array(vertices), np.array(faces)


class OBJ:
    def __init__(self, filename, swapyz=True):
        """Loads a Wavefront OBJ file. """
        self.vertices = []
        self.normals = []
        self.texcoords = []
        self.faces = []
        self.clean_faces = []

        material = None
        for line in open(filename, "r"):
            if line.startswith('#'): continue
            values = line.split()
            if not values: continue
            if values[0] == 'v':
                v = values[1:4]
                if swapyz:
                    v = [v[0], v[2], v[1]]
                self.vertices.append(np.array([v[0], v[1], v[2]], dtype=float))
            elif values[0] == 'vn':
                v = map(float, values[1:4])
                if swapyz:
                    v = v[0], v[2], v[1]
                self.normals.append(v)
            elif values[0] == 'vt':
                self.texcoords.append(map(float, values[1:3]))
            elif values[0] in ('usemtl', 'usemat'):
                material = values[1]
            # elif values[0] == 'mtllib':
            #     self.mtl = MTL(values[1])
            elif values[0] == 'f':
                face = []
                texcoords = []
                norms = []
                for v in values[1:]:
                    w = v.split('/')
                    face.append(int(w[0]))
                    if len(w) >= 2 and len(w[1]) > 0:
                        texcoords.append(int(w[1]))
                    else:
                        texcoords.append(0)
                    if len(w) >= 3 and len(w[2]) > 0:
                        norms.append(int(w[2]))
                    else:
                        norms.append(0)
                self.faces.append((face, norms, texcoords, material))
                if len(face) == 3:
                    self.clean_faces.append([f for f in face])



def normal(face):
    # face is a list of vertices
    p1, p2, p3 = face
    U = p2 - p1 
    V = p3 - p1
    
    x = U[1]*V[2] - U[2]*V[1]
    y = U[2]*V[0] - U[0]*V[2]
    z = U[0]*V[1] - U[1]*V[0]
    
    return normalize( [[x,y,z]], norm='l2').ravel()

def upfacing(normal):
    return int(bool(abs(np.dot(normal, [0,1,0]))>.5))




class OFF(object):
    
    colors = [
        [0, 0, 0],
        [10, 10, 10]
    ]

    def __init__(self, filename):
        self.vertices = []
        self.vertcolors = []
        self.facecolors = []
        self.texcoords = []
        self.faces = []
        self.clean_faces = []
        self.newfacecolors = []
        self.faceneighbor_index = []

        file =  open(filename, "r")

        if 'OFF' not in file.readline().strip():
            raise
        
        n_verts, n_faces, n_dontknow = tuple([int(s) for s in file.readline().strip().split(' ')])
        print ('reading vertices')
        for i_vert in tqdm(range(n_verts), total=n_verts):
            d = file.readline().strip().split(' ')
            self.vertices.append(np.array([d[0], d[1], d[2]], dtype=float))
            self.vertcolors.append(np.array([d[3], d[4], d[5], d[6]], dtype=int))
        
        faces = []
        print ('reading faces')
        for i_face in tqdm(range(n_faces), total=n_faces):
            d = file.readline().strip().split(' ')
            self.faces.append(np.array([d[1], d[2], d[3]], dtype=int))
            self.facecolors.append(np.array([d[4], d[5], d[6]], dtype=int))
        self.faces = np.array(self.faces)
        self.create_vertex_index()


    def create_vertex_index(self):
        print ('creating vertex neighbor index')
        for i, f in tqdm(enumerate(self.faces), total=len(self.faces)):
            hood = np.unique(np.where(np.isin(self.faces, [v for v in f]))[0])
            self.faceneighbor_index.append(hood)
        
    def calculate_new_colors(self):
        print ('creating facecolors')
        for i, f in tqdm(enumerate(self.faces),  total=len(self.faces)):    
            a, b, c  = f
            face = [self.vertices[a], self.vertices[b], self.vertices[c]]
            self.newfacecolors.append(self.colors[upfacing(normal(face))])
            
        print ('averaging facecolors')
        for i, f in tqdm(enumerate(self.faces),  total=len(self.faces)):
            neighbors = self.faceneighbor_index[i]
            c = np.array(self.newfacecolors[i])
            for f in neighbors:
                c +=  np.array(self.newfacecolors[f])
            self.newfacecolors[i] = [c[0], c[1], c[2]]
        

    def write_out_off(self, name):
        
        with open(name, 'w') as out:
            out.write('COFF\n')
            out.write(
                ' '.join(
                        [
                            str(len(self.vertices)), 
                            str(len(self.faces)),
                            str(0)
                        ] 
                )+ '\n'

            )
            print ('writing file')
            for i, v in tqdm(enumerate(self.vertices), total=len(self.vertices)):
                out.write(' '.join([str(p) for p in v]))
                out.write(' ')
                out.write(' '.join([str(c) for c in self.vertcolors[i]]))
                out.write('\n')

            for i, f in tqdm(enumerate(self.faces), total=len(self.faces)):
                out.write(str(len(v)))
                out.write(' ')
                out.write(' '.join([str(v) for v in f]))
                out.write(' ')
                out.write(' '.join([str(c) for c in self.newfacecolors[i]]))
                out.write('\n')
            out.close()

off = OFF('test2_mesh_maya_export.off')
off.calculate_new_colors()
off.write_out_off('out.off')