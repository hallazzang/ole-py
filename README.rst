======
ole-py
======

MS OLE file parser in pure Python.
You can read the details of MS OLE file(a.k.a Compound File) `here
<https://msdn.microsoft.com/ko-kr/library/dd942138.aspx>`_.

Quickstart
----------

.. code:: python

    from ole import OleFile
    
    f = OleFile('testfile.hwp')
    
    for path in f.list_entries():
        print('/'.join(path))
        

Result:

.. code::

    PrvImage
    PrvText
    FileHeader
    DocInfo
    DocOptions/_LinkDoc
    BodyText/Section0
    Scripts/DefaultJScript
    Scripts/JScriptVersion
    HwpSummaryInformation
