======
ole-py
======

MS OLE file parser in pure Python.
You can read the details of MS OLE file(a.k.a Compound File) `here
<https://msdn.microsoft.com/ko-kr/library/dd942138.aspx>`_.

Quickstart
----------

List entries:

.. code:: python

    from ole import OleFile

    f = OleFile('testfile.hwp')

    print('ID   SIZE      PATH')
    print('-' * 50)
    for path in f.list_entries(include_storages=False):
        entry = f.get_entry(path)
        name = b'/'.join(x.encode('unicode-escape') for x in path).decode()
        print('%-3d  %-8d  %s' % (entry.id, entry.stream_size, name))

Result:

.. code::

    ID   SIZE      PATH
    --------------------------------------------------
    4    505       \x05HwpSummaryInformation
    12   31042     BodyText/Section0
    2    2160      DocInfo
    11   524       DocOptions/_LinkDoc
    1    256       FileHeader
    5    3461      PrvImage
    6    2046      PrvText
    10   136       Scripts/DefaultJScript
    9    13        Scripts/JScriptVersion

Get stream data:

.. code:: python

    from ole import OleFile

    f = OleFile('testfile.hwp')

    print('Preview text:')
    print(f.get_stream('PrvText').decode('utf-16le'))

Result:

.. code::

    Preview text:
    2018년 육군 전문특기병(어학병 포함) 모집 일정
    <특기명><모집인원><접수기간><1차발표><면접일시><면접장소><최종발표><입영시기>
    <영어어학병><55><2017-11-03><~><2017-11-14><2017-11-14><2017-12-07   2017-12-07><09:00
    14:00><합동군사대학교   국방어학원><2017-12-22><18년 1~3월><66><2018-01-25><~><2018-02-08><2018-02-08><2018-03-08   2018-03-08><09:00  14:00><2018-03-23><18년 4~6월><64><2018-04-25><~><2018-05-09><2018-05-09><2018-06-07   2018-06-07><09:00  14:00><2018-06-22><18년 7~9월><65><2018-07-25><~><2018-08-09><2018-08-09><2018-09-06   2018-09-06><09:00  14:00><2018-09-21><18년 10~12월>
    <프랑스어어학병><1><2018-05-24><~><2018-06-07><없음><2018-07-04><13:00><2018-07-27><18년 8월><1><2018-09-27><~><2018-10-11><없음><2018-11-06><13:00><2018-11-23><18년 12월>
    <스페인어어학병><1><2018-04-25><~><2018-05-09><없음><2018-06-12><13:00><2018-06-22><18년 7월><1><2018-09-27><~><2018-10-11><없음><2018-11-07><13:00><2018-11-23><18년 12월>
    <독일어어학병><1><2017-11-03><~><2017-11-14><없음><2017-12-04><13:00><2017-12-22><18년 1월><2><2018-05-24><~><2018-06-07><없음><2018-07-05><13:00><2018-07-27><18년 8월>
    <일본어어학병><2><2017-11-03><~><>椄
