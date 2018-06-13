# fitdecode
#
# Copyright (c) 2018 Jean-Charles Lefebvre
# All rights reserved.
#
# This code is licensed under the MIT License.
# See the LICENSE.txt file at the root of this project.

from .reader import FitReader

__all__ = ['FitDecoder']


class FitDecoder:
    """
    Read the entire content of a ``.fit`` file at once, then decode and
    consolidate its data.

    Decoded messages can then be iterated by the caller.

    This class uses `fitdecode.reader.FitReader` internally.
    """

    def __init__(self, fileish, *,
                 processor=None, check_crc=True, keep_raw_chunks=False):
        self._frames = list(FitReader(
            fileish=fileish, processor=processor, check_crc=check_crc,
            keep_raw_chunks=keep_raw_chunks))

        self.files = []  # one element per "FIT file" (i.e. a list of a list of messages?)

        raise NotImplementedError  # TODO
