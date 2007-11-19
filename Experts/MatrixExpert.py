#!/usr/bin/env python
# MatrixExpert.py
#   Copyright (C) 2006 CCLRC, Graeme Winter
#
#   This code is distributed under the BSD license, a copy of which is 
#   included in the root directory of this package.
# 
# 24th July 2007
# 
# A small expert to handle orientation matrix calculations.
# 

import os
import sys
import math

if not os.environ.has_key('XIA2CORE_ROOT'):
    raise RuntimeError, 'XIA2CORE_ROOT not defined'

if not os.environ.has_key('XIA2_ROOT'):
    raise RuntimeError, 'XIA2_ROOT not defined'

if not os.path.join(os.environ['XIA2CORE_ROOT'], 'Python') in sys.path:
    sys.path.append(os.path.join(os.environ['XIA2CORE_ROOT'], 'Python'))

if not os.environ['XIA2_ROOT'] in sys.path:
    sys.path.append(os.environ['XIA2_ROOT'])

from Experts.SymmetryExpert import symop_to_mat
from Wrappers.CCP4.Othercell import Othercell
from lib.SymmetryLib import lattice_to_spacegroup
from Handlers.Syminfo import Syminfo
from Wrappers.Phenix.LatticeSymmetry import LatticeSymmetry

from ReferenceFrame import mosflm_to_xia2, xia2_to_mosflm

# jiffies to convert matrix format (messy)

def mat2vec(mat):
    return [[mat[0], mat[3], mat[6]],
            [mat[1], mat[4], mat[7]],
            [mat[2], mat[5], mat[8]]]

def vec2mat(vectors):
    return [vectors[0][0], vectors[1][0], vectors[2][0],
            vectors[0][1], vectors[1][1], vectors[2][1],
            vectors[0][2], vectors[1][2], vectors[2][2]]

# generic mathematical calculations for 3-vectors

# FIXME cite PRE as the source here for these rotns

def rot_x(theta):
    '''Rotation matrix about Y of theta degrees.'''

    dtor = 180.0 / (4.0 * math.atan(1.0))

    c = math.cos(theta / dtor)
    s = math.sin(theta / dtor)

    return [1.0, 0.0, 0.0, 0.0, c, s, 0.0, -s, c]

def rot_y(theta):
    '''Rotation matrix about Y of theta degrees.'''

    dtor = 180.0 / (4.0 * math.atan(1.0))

    c = math.cos(theta / dtor)
    s = math.sin(theta / dtor)

    return [c, 0.0, -s, 0.0, 1.0, 0.0, s, 0.0, c]

def rot_z(theta):
    '''Rotation matrix about Y of theta degrees.'''

    dtor = 180.0 / (4.0 * math.atan(1.0))

    c = math.cos(theta / dtor)
    s = math.sin(theta / dtor)

    return [c, -s, 0.0, s, c, 0.0, 0.0, 0.0, 1.0]

def b_matrix(a, b, c, alpha, beta, gamma):
    '''Generate a B matric from a unit cell. Cite: Pflugrath in Methods
    Enzymology 276.'''

    dtor = 180.0 / (4.0 * math.atan(1.0))

    ca = math.cos(alpha / dtor)
    sa = math.sin(alpha / dtor)
    cb = math.cos(beta / dtor)
    sb = math.sin(beta / dtor)
    cg = math.cos(gamma / dtor)
    sg = math.sin(gamma / dtor)

    # invert the cell parameters
    # CITE: International Tables C Section 1.1
    
    V = a * b * c * math.sqrt(1 - ca * ca - cb * cb - cg * cg +
                              2 * ca * cb * cg)

    a_ = b * c * sa / V
    b_ = a * c * sb / V
    c_ = a * b * sg / V

    # NOTE well - these angles are in radians
    
    alpha_ = math.acos((cb * cg - ca) / (sb * sg))
    beta_ = math.acos((ca * cg - cb) / (sa * sg))
    gamma_ = math.acos((ca * cb - cg) / (sa * sb))
 
    ca_ = math.cos(alpha_)
    sa_ = math.sin(alpha_)
    cb_ = math.cos(beta_)
    sb_ = math.sin(beta_)
    cg_ = math.cos(gamma_)
    sg_ = math.sin(gamma_)
   
    # NEXT construct the B matrix - CITE Pflugrath in Methods E 276

    return [a_, b_ * cg_, c_ * cb_,
            0.0, b_ * sg_, - c_ * sb_ * ca_,
            0.0, 0.0, c_ * sb_ * sa_]

def dot(a, b):
    return sum([a[j] * b[j] for j in range(3)])

def cross(a, b):
    return [a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0]]

def vecscl(vector, scale):
    return [vector[j] * scale for j in range(len(vector))]

def matscl(matrix, scale):
    return [matrix[j] * scale for j in range(len(matrix))]

def invert(matrix):
    vecs = mat2vec(matrix)
    scl = 1.0 / dot(vecs[0], cross(vecs[1], vecs[2]))

    return transpose(
        vec2mat([vecscl(cross(vecs[1], vecs[2]), scl),
                 vecscl(cross(vecs[2], vecs[0]), scl),
                 vecscl(cross(vecs[0], vecs[1]), scl)]))

def transpose(matrix):
    return [matrix[0], matrix[3], matrix[6],
            matrix[1], matrix[4], matrix[7],
            matrix[2], matrix[5], matrix[8]]
            
def det(matrix):
    vecs = mat2vec(matrix)
    return dot(vecs[0], cross(vecs[1], vecs[2]))
    
def matmul(b, a):
    avec = mat2vec(transpose(a))
    bvec = mat2vec(b)

    result = []
    for i in range(3):
        for j in range(3):
            result.append(dot(avec[i], bvec[j]))

    return result

def matvecmul(M, v):
    '''Multiply a vector v by a matrix M -> return M v.'''

    Mvec = mat2vec(transpose(M))
    result = []
    for i in range(3):
        result.append(dot(Mvec[i], v))
    return result

# things specific to mosflm matrix files...

def parse_matrix(matrix_text):
    '''Parse a matrix returning cell, a and u matrix.'''

    # this will need to be able to cope with the times
    # when the matrix includes columns merging together
    # (which sucks)

    # therefore parse this manually... or just add
    # a space before all '-'

    tokens = map(float, matrix_text.replace('-', ' -').split())

    cell = tokens[21:27]
    a = tokens[0:9]
    u = tokens[12:21]

    return cell, a, u

def format_matrix(cell, a, u):
    matrix_format = ' %11.8f %11.8f %11.8f\n' + \
                    ' %11.8f %11.8f %11.8f\n' + \
                    ' %11.8f %11.8f %11.8f\n'
    
    cell_format = ' %11.4f %11.4f %11.4f %11.4f %11.4f %11.4f\n'
    
    misset = '       0.000       0.000       0.000\n'

    return matrix_format % tuple(a) + misset + matrix_format % tuple(u) + \
           cell_format % tuple(cell) + misset

def transmogrify_matrix(lattice, matrix, target_lattice):
    '''Transmogrify a matrix for lattice X into a matrix for lattice
    Y. This should work find for Mosflm... Will also return the new
    unit cell.'''

    cell, a, u = parse_matrix(matrix)

    o = Othercell()
    o.set_cell(cell)
    o.set_lattice(lattice[1].lower())
    o.generate()

    new_cell = o.get_cell(target_lattice)
    op = symop_to_mat(o.get_reindex_op(target_lattice))

    a = matmul(invert(op), a)
    u = matmul(op, u)

    return format_matrix(new_cell, a, u)
    
def get_real_space_primitive_matrix(lattice, matrix):
    '''Get the primitive real space vectors for the unit cell and
    lattice type. Note that the resulting matrix will need to be
    scaled by a factor equal to the wavelength in Angstroms.'''

    # parse the orientation matrix 
    
    cell, a, u = parse_matrix(matrix)

    # generate other possibilities

    o = Othercell()
    o.set_cell(cell)
    o.set_lattice(lattice[1].lower())
    o.generate()

    # transform the possibly centred cell to the primitive setting

    new_cell = o.get_cell('aP')
    op = symop_to_mat(o.get_reindex_op('aP'))

    primitive_a = matmul(invert(op), a)

    # then convert to real space

    real_a = invert(primitive_a)

    return real_a[0:3], real_a[3:6], real_a[6:9]

def get_reciprocal_space_primitive_matrix(lattice, matrix):
    '''Get the primitive reciprocal space vectors for this matrix.'''

    # parse the orientation matrix 
    
    cell, a, u = parse_matrix(matrix)

    # generate other possibilities

    o = Othercell()
    o.set_cell(cell)
    o.set_lattice(lattice[1].lower())
    o.generate()

    # transform the possibly centred cell to the primitive setting

    new_cell = o.get_cell('aP')
    op = symop_to_mat(o.get_reindex_op('aP'))

    primitive_a = matmul(invert(op), a)

    return mat2vec(primitive_a)

def find_primitive_axes(lattice, matrix):
    '''From an orientation matrix file, calculate the angles (phi) where
    the primitive cell axes a, b, c are in the plane of the detector
    (that is, orthogonal to the direct beam vector.'''

    a, b, c = get_real_space_primitive_matrix(lattice, matrix)

    dtor = 180.0 / (4.0 * math.atan(1.0))

    return (dtor * math.atan( - a[2] / a[0]), \
            dtor * math.atan( - b[2] / b[0]), \
            dtor * math.atan( - c[2] / c[0]))

def find_primitive_reciprocal_axes(lattice, matrix):
    '''From an orientation matrix file, calculate the angles (phi) where
    the primitive reciprical space cell axes a, b, c are in the plane of
    the detector (that is, orthogonal to the direct beam vector.'''

    a, b, c = get_reciprocal_space_primitive_matrix(lattice, matrix)

    dtor = 180.0 / (4.0 * math.atan(1.0))

    return (dtor * math.atan( - a[2] / a[0]), \
            dtor * math.atan( - b[2] / b[0]), \
            dtor * math.atan( - c[2] / c[0]))

def mosflm_a_matrix_to_real_space(wavelength, lattice, matrix):
    '''Given a Mosflm A matrix and the associated spacegroup (think of this
    Bravais lattice (which will be converted to a spacegroup for the benefit
    of the CCTBX program lattice_symmetry) return the real space primative
    crystal lattice vectors in the xia2 reference frame. This reference frame
    corresponds to that defined for imgCIF.'''

    # convert the lattice to a spacegroup
    spacegroup_number = lattice_to_spacegroup(lattice)
    spacegroup = Syminfo.spacegroup_name_to_number(spacegroup_number)

    # get the a, u, matrices and the unit cell
    cell, a, u = parse_matrix(matrix)

    # use iotbx.latice_symmetry to obtain the reindexing operator to
    # a primative triclinic lattice
    ls = LatticeSymmetry()
    ls.set_cell(cell)
    ls.set_spacegroup(spacegroup)
    cell, reindex = ls.generate_primative_reindex()

    reindex_matrix = symop_to_mat(reindex)

    # scale the a matrix
    a = matscl(a, 1.0 / wavelength)

    # convert to real space (invert) and apply this reindex operator to the a
    # matrix to get the primative real space triclinic cell axes
    real_a = matmul(reindex_matrix, transpose(invert(a)))

    # convert these to the xia2 reference frame
    a, b, c = mat2vec(real_a)
    ax = mosflm_to_xia2(a)
    bx = mosflm_to_xia2(b)
    cx = mosflm_to_xia2(c)

    # return these vectors
    return ax, bx, cx

if __name__ == '__main__':
    matrix = ''' -0.00417059 -0.00089426 -0.01139821
 -0.00084328 -0.01388561  0.01379631
 -0.00121258  0.01273236  0.01424531
      -0.099       0.451      -0.013
 -0.94263428 -0.04741397 -0.33044314
 -0.19059871 -0.73622239  0.64934635
 -0.27406719  0.67507666  0.68495023
    228.0796     52.5895     44.1177     90.0000    100.6078     90.0000
     -0.0985      0.4512     -0.0134'''

    a, b, c = mosflm_a_matrix_to_real_space(0.99187, 'mC', matrix)

    print math.sqrt(dot(a, a))
    print math.sqrt(dot(b, b))
    print math.sqrt(dot(c, c))

if __name__ == '__main_old__':

    matrix = ''' -0.00417059 -0.00089426 -0.01139821
 -0.00084328 -0.01388561  0.01379631
 -0.00121258  0.01273236  0.01424531
      -0.099       0.451      -0.013
 -0.94263428 -0.04741397 -0.33044314
 -0.19059871 -0.73622239  0.64934635
 -0.27406719  0.67507666  0.68495023
    228.0796     52.5895     44.1177     90.0000    100.6078     90.0000
     -0.0985      0.4512     -0.0134'''

    print transmogrify_matrix('mC', matrix, 'aP')
    
    a, b, c = get_real_space_primitive_matrix('mC', matrix)

    print math.sqrt(dot(a, a)), math.sqrt(dot(b, b)), math.sqrt(dot(c, c))

    # to get the phi values am most interested in Ra.Z, Rb.Z, Rc.Z.
    # this is trivial to calculate:
    # R(t)x.z = 0 => x_1 sin(t) = x_3 cos(t) => t = atan(x_3 / x_1)

    dtor = 180.0 / (4.0 * math.atan(1.0))

    print dtor * math.atan(a[2] / a[0]), dtor * math.atan(b[2] / b[0]), \
          dtor * math.atan(c[2] / c[0])

if __name__ == '__main_dtrek__':

    # this lot should end up as a unit test which tests out the
    # b matrix, cell inversion, rotations and so on - the end
    # cell should be identical to the beginning one!

    a = 57.8349
    b = 77.2950
    c = 86.7453
    alpha = 90.0
    beta = 90.0
    gamma = 90.0

    bmat = b_matrix(a, b, c, alpha, beta, gamma)
    m = matmul(rot_z(-18.467), matmul(rot_y(-3.227),
                                      matmul(rot_x(-55.432), bmat)))
    u = matmul(m, invert(bmat))
    print '%.6f %.6f %.6f\n%.6f %.6f %.6f\n%.6f %.6f %.6f\n' % tuple(u)
    rm = invert(m)
    print '%.6f %.6f %.6f\n%.6f %.6f %.6f\n%.6f %.6f %.6f\n' % tuple(rm)

    cell = transpose(rm)
    print math.sqrt(cell[0] * cell[0] + cell[1] * cell[1] + cell[2] * cell[2])
    print math.sqrt(cell[3] * cell[3] + cell[4] * cell[4] + cell[5] * cell[5])
    print math.sqrt(cell[6] * cell[6] + cell[7] * cell[7] + cell[8] * cell[8])
    
    _a, _b, _c = tuple(mat2vec(rm))

    dtor = 180.0 / (4.0 * math.atan(1.0))

    print math.acos(dot(_b, _c) / math.sqrt(dot(_b, _b) * dot(_c, _c))) * dtor
    print math.acos(dot(_c, _a) / math.sqrt(dot(_a, _a) * dot(_c, _c))) * dtor
    print math.acos(dot(_a, _b) / math.sqrt(dot(_a, _a) * dot(_b, _b))) * dtor
    

if __name__ == '__main_xds__':

    m = (0.00095924, 0.01043167, 0.00642292,
         0.00537416, 0.00667498, -0.00892183,
         -0.01604217, 0.00285989, -0.00260477)

    # unrefined
    m = (0.000957550, 0.01040052, 0.00641526,
         0.00536470, 0.00665505, -0.00891111,
         -0.01601392, 0.00285135, -0.00260164)
    
    m2 = []
    for k in m:
        m2.append(k / 0.9795)
    m = tuple(m2)
    cell = tuple(invert(m))
    print '%.4f %.4f %.4f\n%.4f %.4f %.4f\n%.4f %.4f %.4f\n' % cell
    print math.sqrt(cell[0] * cell[0] + cell[1] * cell[1] + cell[2] * cell[2])
    print math.sqrt(cell[3] * cell[3] + cell[4] * cell[4] + cell[5] * cell[5])
    print math.sqrt(cell[6] * cell[6] + cell[7] * cell[7] + cell[8] * cell[8])

    r = (0, 0, 1, 0, 1, 0, -1, 0, 0)

    print '%.6f %.6f %.6f\n%.6f %.6f %.6f\n%.6f %.6f %.6f\n' % tuple(matmul(r, cell))

if __name__ == '__main__j':
    if len(sys.argv) < 3:

        lattice = 'mC'

        matrix = ''' -0.00417059 -0.00089426 -0.01139821
 -0.00084328 -0.01388561  0.01379631
 -0.00121258  0.01273236  0.01424531
      -0.099       0.451      -0.013
 -0.94263428 -0.04741397 -0.33044314
 -0.19059871 -0.73622239  0.64934635
 -0.27406719  0.67507666  0.68495023
    228.0796     52.5895     44.1177     90.0000    100.6078     90.0000
     -0.0985      0.4512     -0.0134'''

    else:
        lattice = sys.argv[1]
        matrix = open(sys.argv[2], 'r').read()

    print '%.2f %.2f %.2f' % find_primitive_axes(
        lattice, matrix)

    print '%.2f %.2f %.2f' % find_primitive_reciprocal_axes(
        lattice, matrix)
    
if __name__ == '__main__vecmul':
    M = (0, 1, 0, 1, 0, 0, 0, 0, 1)
    v = (1, 2, 3)

    print '%f %f %f' % tuple(matvecmul(M, v))
    
    M = (2, 0, 0, 0, 2, 0, 0, 0, 2)
    
    print '%f %f %f' % tuple(matvecmul(M, v))    
