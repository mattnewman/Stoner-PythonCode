"""Stoner.hdf5 Defines classes that use the hdf5 file format to store data on disc.
Classes include

* \b HDF5File - A \b DataFile subclass that can save and load data from hdf5 files
* \b HDF5Folder - A \b DataFolder subclass that can save and load data from a single hdf5 file

"""

import h5py
import numpy
from .Core import DataFile
from .Folders import DataFolder
import os.path as path

class HDF5File(DataFile):
    """A sub class of DataFile that sores itself in a HDF5File or group.
    Overloads self.load and self.save
    
        Datalayout is dead simple, the numerical data is in a dataset called 'data',
        metadata are attribtutes of a group called metadata with the keynames being the
        full name + typehint of the stanard DataFile metadata dictionary
        column_headers are an attribute of the root file/group
        filename is set from either an attribute called filename, or from the
        group name or from the hdf5 filename.
        The root has an attribute 'type' that must by 'HDF5File' otherwise the load routine
        will refuse to load it. This is to try to avoid loading rubbish from random hdf files.

    """
    
    priority=32
    compression='gzip'
    compression_opts=6
    
    def __init__(self,*args,**kargs):
        """Constructor to catch initialising with an h5py.File or h5py.Group
        @param args Tuple of supplied arguments, only recognises one though !
        @param kargs Dictionary of keyword arguments
        
        If the first non-keyword arguement is not an h5py File or Group then
        initialises with a blank parent constructor and then loads data, otherwise,
        calls parent constructor.
        """
        if len(args)>0:
            other=args[0]
            if isinstance(other,h5py.File) or isinstance(other,h5py.Group):
                super(HDF5File,self).__init__(**kargs)
                self.load(other,**kargs)
            else:
                super(HDF5File,self).__init__(*args,**kargs)
    
    def load(self,h5file,**kargs):
        """Loads data from a hdf5 file
        @param h5file Either a string or an h5py Group object to load data from
        @return itself after having loaded the data
        
        
        """
        if isinstance(h5file,str) or isinstance(h5file,unicode): #We got a string, so we'll treat it like a file...
            try:
                f=h5py.File(h5file,'r')
            except IOError:
                raise IOError("Failed to open {} as a n hdf5 file".format(h5file))
        elif isinstance(h5file,h5py.File) or isinstance(h5file,h5py.Group):
            f=h5file
        else:
            raise IOError("Couldn't interpret {} as a valid HDF5 file or group or filename".format(h5file))
        if "type" in f.attrs: #Ensure that if we have a type attribute it tells us we're the right type !
            assert f.attrs["type"]=="HDF5File","HDF5 group doesn't hold an HD5File"
        data=f["data"]
        if numpy.product(numpy.array(data.shape))>0:
            self.data=data[...]
        else:
            self.data=[[]]
        metadata=f.require_group('metadata')
        self.column_headers=f.attrs["column_headers"]
        for i in metadata.attrs:
            self[i]=metadata.attrs[i]
        if "filename" in f.attrs:
            self.filename=f.attrs["filename"]
        elif isinstance(f,h5py.Group):
            self.filename=f.name
        else:
            self.filename=f.file.filename
            
        if isinstance(h5file,str):
            f.file.close()
        return self
        
    def save(self,h5file):
        """Writes the current object into  an hdf5 file or group within a file in a 
        fashion that is compatible with being loaded in again with the same class.
        @param h5file Either a string, of h5py.File or h5py.Group object into which
        to save the file. If this is a string, the corresponding file is opened for
        writing, written to and save again.
        @return A copy of the object
        """
        if isinstance(h5file,str):
            f=h5py.File(h5file,'w')
        elif isinstance(h5file,h5py.File) or isinstance(h5file,h5py.Group):
            f=h5file
        try:
            data=f.require_dataset("data",data=self.data,shape=self.data.shape,dtype=self.data.dtype,compression=self.compression,compression_opts=self.compression_opts)
            data=self.data
            metadata=f.require_group("metadata")
            for k in self.metadata:
                try:
                    metadata.attrs[k]=self[k]
                except TypeError: # We get this for trying to store a bad data type - fallback to metadata export to string
                    parts=self.metadata.export(k).split('=')
                    metadata[parts[0]]="=".join(parts[1:])
            f.attrs["column_headers"]=self.column_headers
            f.attrs["filename"]=self.filename
            f.attrs["type"]="HDF5File"
        except Exception as e:
            if isinstance(h5file,str):
                f.file.close()
            raise e
        if isinstance(h5file,str):
            f.file.close()
        
        return self
        
class HDF5Folder(DataFolder):
    """A sub class of DataFolder that provides a method to load and save data from a single HDF5 file with groups.
    
    Datalayout consistns of sub-groups that are either instances of HDF5Files (i.e. have a type attribute that contains 'HDF5File')
    or are themsleves HDF5Folder instances (with a type attribute that reads 'HDF5Folder').
    
    """

    def __init__(self,*args,**kargs):
        """Constructor for the HDF5Folder Class.
        """
        self.files=[]
        self.groups={}
        self.File=None
        self.type=HDF5File
        for k in ["pattern","type","File","directory"]:
            if k in kargs:
                self.__dict__[k]=kargs[k]
        if len(args)>0 and (isinstance(args[0],str) or isinstance(args[0],unicode)): # Very braindead here, we should recognise pattern and a few other things here
            self.directory=args[0]
            if "nolist" in kargs and isinstance(kargs["nolist",bool]) and kargs["nolist"]:
                pass
            else:
                self.getlist()
        elif len(args)>0 and isinstance(args[0],DataFolder):
            super(HDF5Folder,self).__init__(*args)
        elif len(args)==1 and isinstance(args[0],h5py.File) or isinstance(args[0],h5py.Group):
            grp=args[0]
            self.directory=grp.file.fielname
            self.File=grp.file
            if "nolist" in kargs and isinstance(kargs["nolist",bool]) and kargs["nolist"]:
                pass
            else:
                self.getlist()
        else:   
            raise RuntimeError('Bad Constructor !')        
    
    def _dialog(self, message="Select Folder",  new_directory=True,mode='r'):
        """Creates a file dialog box for working with

        @param message Message to display in dialog
        @param new_file True if allowed to create new directory
        @return A directory to be used for the file operation."""
        try:
            from enthought.pyface.api import FileDialog, OK
        except ImportError:
            from pyface.api import FileDialog, OK
        # Wildcard pattern to be used in file dialogs.
        file_wildcard = "hdf file (*.hdf5)|*.hdf5|Data file (*.dat)|\
        *.dat|All files|*"

        if mode == "r":
            mode2 = "open"
        elif mode == "w":
            mode2 = "save as"

        if self.directory is not None:
            filename = path.basename(path.realpath(self.directory))
            dirname = path.dirname(path.realpath(self.directory))
        else:
            filename = ""
            dirname = ""
        dlg = FileDialog(action=mode2, wildcard=file_wildcard)
        dlg.open()
        if dlg.return_code == OK:
            self.directory = dlg.path
            self.File=h5py.File(self.directory,mode)
            self.File.close()
            return self.directory
        else:
            return None

    def getlist(self, recursive=True, directory=None):
        """@TODO Write the HDF5Folder getlist function"""
        self.files=[]
        self.groups={}
        for d in [directory,self.directory,self.File,True]:
            if isinstance(d,bool) and d:
                d=self._dialog()
            directory=d
            if d is not None:
                break
        if directory is None:
            return None
        if isinstance(directory,str) or isinstance(directory,unicode):
            self.directory=directory
            directory=h5py.File(directory,'r')
            self.File=directory
        elif isinstance(directory,h5py.File) or isinstance(directory,h5py.Group):
            self.File=directory.file
            self.directory=self.File.filename
        #At this point directory contains an open h5py.File object, or possibly a group
        for obj in directory:
            obj=directory[obj]
            if isinstance(obj,h5py.Group) and "type" in obj.attrs:
                if obj.attrs["type"]=="HDF5File":
                    self.files.append(obj.name)
                elif obj.attrs["type"]=="HDF5Folder" and recursive:
                    self.groups[obj.name.split(path.sep)[-1]]=self.__class__(obj,pattern=self.pattern,type=self.type)
                else:
                    raise IOError("Found a group {} that isn't recognised".format(obj.name))

        return self
        
        
    def __read__(self,f):
        """Override the _-read method to handle pulling files from the HD5File"""
        if isinstance(f,DataFile): # This is an already loaded DataFile
            tmp=f
            f=tmp.filename
        elif isinstance(f,h5py.Group) or isinstance(f,h5py.File): # This is a HDF5 file or group
            tmp=HDF5File(f)
            f=f.name
        elif isinstance(f,str) or isinstance(f,unicode): #This sis a string, so see if it maps to a path in the current File
            if f in self.File and "type" in self.File[f].attrs and self.File[f].attrs["type"]=="HDF5File":
                tmp=HDF5File(self.File[f])
            else: # Otherwise fallback and try to laod from disc
                tmp= super(HDF5Folder,self).__read__(f)
        else:
            raise RuntimeError("Unable to workout how to read from {}".format(f))
        tmp["Loaded from"]=f
        if self.read_means:
            if len(tmp)==0:
                pass
            elif len(tmp)==1:
                for h in tmp.column_headers:
                    tmp[h]=tmp.column(h)[0]
            else:
                for h in tmp.column_headers:
                    tmp[h]=numpy.mean(tmp.column(h))

        return tmp
            
    def save(self,root=None):
        """Saves a load of files to a single HDF5 file, creating groups as it goes.
        @param root The name of the HDF5 file to save to if set to None, will prompt for a filename.
        @return A list of group paths in the HDF5 file
        """
        
        if root is None:
            root=self._dialog(mode='w')
        elif isinstance(root,bool) and not root and isinstance(self.File,h5py.File):
            root=self.File.filename
            self.File.close()
        self.File=h5py.File(root,'w')
        tmp=self.walk_groups(self._save,walker_args={"root":root})
        self.File.file.close()
        return tmp
        
    def _save(self,f,trail,root):
        """Ensure we have created the trail as a series of sub groups, then create a sub-groupfor the filename
        finally cast the DataFile as a HDF5File and save it, passing the new group as the filename which
        will ensure we create a sub-group in the main HDF5 file
        @param f A DataFile instance
        @param trail The trail of groups
        @param root the starting HDF5 File.
        @return the new filename
        """
        tmp=self.File
        if not isinstance(f,DataFile):
            f=DataFile(f)
        for g in trail:
            if g not in tmp:
                tmp.create_group(g)
            tmp=tmp[g]
        tmp.create_group(f.filename)
        tmp=tmp[f.filename]
        f=HDF5File(f)
        f.save(tmp)
        return f.filename
            
        
            
            
        
    