"""
Messages
    -

D. Kotlyar

Functions:
    - fuel_branch: main function that creates a modified file with perturbed conditions
    - perturb_bumat: Modifies the temperature and prefix for a specific material
    - get_materials_bumat: scraps the modified names in _bumat file
    - match_materials: compares between the modified and the original names of the materials.

Note: the number of branched materials should be equal to the number
of original materials
"""

import os
import re

import xsboa.messages as messages


def fuel_branch(inpfile, outfile, mat_list, tmp_list, prf_list, args=None):
    """
    :param inpfile: the name of the _bumat file
    :param outfile: the name of the perturbed file
    :param mat_list: a list that contains the names of all materials
                ['fuel1', 'fuel2', 'fuel3', 'fuel4', 'fuel5', 'fuel22']
    :param tmp_list: a list that contains the temperatures of all materials in Kelvins
                ['900', '900', '670', '580', '920', '1055']
    :param prf_list: a list that contains the prefixes of all materials
                ['.09c', '.09c', '.06c', '.06c', '.09c', '.10c']
    :param args:
    :return:
    """

    if args is None:
        args = {'verbose': True, 'output': None}

    if not os.path.exists(inpfile):
        messages.warn('File {} does not exist and cannot be scraped'.format(os.path.join(os.getcwd(), inpfile)),
                      'fuel_branch()', args)
        return -1

    if len(mat_list) != len(tmp_list):  # otherwise ok
        messages.warn('The number of temperatures {0} and materials {1} is not equal'.format(len(tmp_list),
                                                                                             os.path.join(os.getcwd(),
                                                                                                          inpfile),
                                                                                             len(mat_list)),
                      'fuel_branch()', args)
        return -2

    if len(mat_list) != len(prf_list):  # otherwise ok
        messages.warn('The number of temperatures {0} and materials {1} is not equal'.format(len(prf_list),
                                                                                             os.path.join(os.getcwd(),
                                                                                                          inpfile),
                                                                                             len(mat_list)),
                      'fuel_branch()', args)
        return -2

    messages.status('Fuel temperature perturbations, processing: {} file ...'.format(inpfile), args)

    # get the modified names from the _bumat file
    flag, mat_list_mod = get_materials_bumat(inpfile, args=None)
    if flag != 0:
        return flag

    # match the original and modified lists
    flag, idx_mat = match_materials(inpfile, mat_list, mat_list_mod, args=None)
    if flag != 0:
        return flag

    for iBurnMat in range(len(mat_list_mod)):  # for each burnable material perturb the conditions
        flag = perturb_bumat(inpfile, outfile, mat_list_mod[iBurnMat], mat_list[idx_mat[iBurnMat][0]],
                             tmp_list[idx_mat[iBurnMat][0]], prf_list[idx_mat[iBurnMat][0]], args=None)
        if flag != 0:
            return flag
    messages.status('Fuel temperature perturbation finished, output: {} file ...'.format(outfile), args)
    return 0


def perturb_bumat(inpfile, outfile, mat, mat_orig, temp, prf, args=None):
    '''
    Perturb the _bumat# file to include the branched conditions (new temperature and prefix)
    :param inpfile: _bumat input file
    :param outfile: the new name of the perturbed file
    :param mat: The name of the burnable material (str)
    :param mat_mod: The name of the original burnable material (str)
    :param temp: The temperature in Kelvins (str)
    :param prf: The prefix for cross-sections, e.g. '.09c' (str)
    :return:
    '''

    # Default matching prefixes and temperatures
    validPrfTypes = ('.03c', '.06c', '.09c', '.12c', '.15c', '.18c')
    validTmpTypes = (300, 600, 900, 1200, 1500, 1800)

    if args is None:
        args = {'verbose': True, 'output': None}

    if not os.path.exists(inpfile):
        messages.warn('File {} does not exist and cannot be scraped'.format(os.path.join(os.getcwd(), inpfile)),
                      'perturb_bumat()', args)
        return -1

    if prf not in validPrfTypes:
        messages.warn('Prefix specifier {0} not supported at this time. Please use one of the following: {1}\n'
                      .format(prf, ' '.join(validPrfTypes)), 'perturb_bumat()', args)
        return -3

    if (float(temp) < validTmpTypes[0]) | (float(temp) > (validTmpTypes[len(validTmpTypes) - 1])):
        messages.warn('The temperature [K] for material {0} is not in the range {1}-{2}. \n'
                      .format(mat, validTmpTypes[0], validTmpTypes[(len(validTmpTypes) - 1)]), 'perturb_bumat()', args)
        return -3

    messages.status('Processing material {}'.format(mat), args)

    fid_in = open(inpfile, 'r')  # original _bumat file
    fid_out = open(outfile, 'a')  # modified (perturbed) _bumatfile

    flag_eof = 0

    # Reset variables
    vol = []  # the volume of the material

    while True:

        if flag_eof == 1:  # end-of-file indicator
            break
        tline = fid_in.readline()  # read every line in the _bumat file
        if tline == '':  # checks end-of-file
            break

        if (mat in tline) & ('mat' in tline):  # material found
            ND = 'sum'
            condV = False
            vars_tline = tline.split()  # separate the variables in the line
            for idx in range(len(vars_tline)):  # loop over the variables in the list
                if vars_tline[idx] == 'vol':  # Register the volume of the material, if given
                    condV = True
                    vol = vars_tline[idx + 1]

                if vars_tline[idx] == mat:  # Register the nuclide density of the material
                    ND = vars_tline[idx + 1]

            if temp == []:
                tline = 'mat   ' + '  ' + mat_orig + '  ' + ND + '  '
            else:
                tline = 'mat   ' + '  ' + mat_orig + '  ' + ND + '  ' + '  tmp  ' + temp

            if condV == True:
                tline = tline + '  vol ' + vol  # print the registered volume

            tline = tline + '\n'
            fid_out.writelines(tline)  # write the new mat line

            # A loop over the nuclides
            while True:
                tline = fid_in.readline()
                if tline == '':  # checks end-of-file
                    flag_eof = 1
                    break
                if tline == '\n':  # empty line
                    fid_out.writelines('\n')
                    flag_eof = 1
                    break
                idxPrf = re.search('\.\d+c', tline)  # identify the prefix

                if idxPrf != None:  # prefix found, e.g. 8016.09c 4.6E-02
                    tline = tline.replace(tline[idxPrf.end() - 4:idxPrf.end()], prf)
                    fid_out.writelines(tline)
                else:
                    fid_out.writelines('\n')
                    break



                    # fid_out.writelines(tline)

    fid_in.close()
    fid_out.close()
    return 0


def get_materials_bumat(inpfile, args=None):
    """
    The function reads the input file and scraps the id's (i.e. names) for all the materials.
    :param inpfile: The _bumat input file
    :param args:
    :return: mat_id: a list that contains all the materials id's
    """
    if args is None:
        args = {'verbose': True, 'output': None}

    mat_id = list()

    if not os.path.exists(inpfile):
        messages.warn('File {} does not exist and cannot be perturbed'.format(os.path.join(os.getcwd(), inpfile)),
                      'get_materials_bumat()', args)
        return -1, mat_id

    fid_in = open(inpfile, 'r')
    # Reset variables
    imat = 0

    # Loop over each separate line: to collect the materials' names (ids)
    while True:

        tline = fid_in.readline()  # read every line in the _bumat file
        if tline == '':  # checks end-of-file
            break

        if 'mat' in tline:  # a material is found

            vars_tline = tline.split()  # separate the variables in the line
            if 'mat' in vars_tline[0]:  # if the string 'mat' appears first than material id would follow
                mat_id.insert(imat, vars_tline[1])  # add the id to the list
                imat += 1  # counts the number of materials

    fid_in.close()
    return 0, mat_id  # a list of material names


def match_materials(inpfile, orig_mat_id, mod_mat_id, args=None):
    """
    The function compares two lists: 1) original-- against 2) modified--names.
    e.g. ('fuel1','fuel2',...) vs. ('fuel1p1r1','fuel2p2r2',...).
    The modified list can contain more components than the original.
    The user can divide the pin into radial regions using the 'burn n' card.
    This will create 'n' modified id's for each original material.
    The perturbed temperature must be included for all the modified materials.

    Note: the number of branched materials should be equal to the number
    of original materials

    :param inpfile: input file.
    :param orig_mat_id: list of all original materials' names (id's).
    :param mod_mat_id: list of all modified materials' names (id's).
    :param args:
    :return: idx_mat: index/position of the modified material in the original list
    """
    if args is None:
        args = {'verbose': True, 'output': None}

    idx_mat = list()  # for each material it includes 3 values: 1) the index in the original id list

    if len(mod_mat_id) != len(orig_mat_id):  # otherwise ok
        messages.warn('There are less burnable materials (={0}) in the {1} file than originally defined (={2})'.format(
            len(mod_mat_id), os.path.join(os.getcwd(), inpfile), len(orig_mat_id)),
            'match_materials()', args)
        return -4, idx_mat

    messages.status('Processing file / match the modified vs. original names {}'.format(inpfile), args)

    # 2) start index of the name in the modified id 3) end index in the modified id
    for imat in range(len(mod_mat_id)):
        idx_mat.insert(imat, [0, 0, 0])  # initialize - this becomes a matrix of size Nx3

    for idx_mod in range(len(mod_mat_id)):
        for idx_orig in range(len(orig_mat_id)):
            idx_match = re.search(orig_mat_id[idx_orig], mod_mat_id[idx_mod])
            if idx_match != None:
                idx_start = idx_match.start()
                idx_end = idx_match.end()
                if (idx_end - idx_start) > (idx_mat[idx_mod][2] - idx_mat[idx_mod][
                    1]):  # current string is longer than the previous one, update
                    idx_mat[idx_mod][0] = idx_orig  # the index of the modified material's name in the original list.
                    idx_mat[idx_mod][1] = idx_start  # start index of the string
                    idx_mat[idx_mod][2] = idx_end  # end index of the string

    return 0, idx_mat

# ----------------------------------------------------------------------
#                        testing
# ----------------------------------------------------------------------
# inpfile = '../testing/SINP020.bumat0'
# outfile = '../testing/perturbed.bumat0'

# mat_test = ['fuel1', 'fuel2', 'fuel11', 'fuel111', 'fuel4']
# prf_test = ['.03c', '.06c', '.09c', '.12c', '.15c']
# tmp_test = ['300', '600', '900', '1200', '1500']

# fuel_branch(inpfile, outfile, mat_test, tmp_test, prf_test, args=None)
# a=1

