#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Decodes qmc[3|0|ogg|flac] files."""

import re
import os
import io
import struct
import logging
import click
import concurrent.futures
from tqdm.auto import tqdm


class Seed(object):
    """Generate next mask bit for decoder"""

    seedMap = [
        [0x4a, 0xd6, 0xca, 0x90, 0x67, 0xf7, 0x52],
        [0x5e, 0x95, 0x23, 0x9f, 0x13, 0x11, 0x7e],
        [0x47, 0x74, 0x3d, 0x90, 0xaa, 0x3f, 0x51],
        [0xc6, 0x09, 0xd5, 0x9f, 0xfa, 0x66, 0xf9],
        [0xf3, 0xd6, 0xa1, 0x90, 0xa0, 0xf7, 0xf0],
        [0x1d, 0x95, 0xde, 0x9f, 0x84, 0x11, 0xf4],
        [0x0e, 0x74, 0xbb, 0x90, 0xbc, 0x3f, 0x92],
        [0x00, 0x09, 0x5b, 0x9f, 0x62, 0x66, 0xa1]
    ]

    def __init__(self, x=-1, y=8, dx=1, index=-1):
        self.x = x
        self.y = y
        self.dx = dx
        self.index = index

    def next_mask(self):
        ret = None
        self.index += 1
        if self.x < 0:
            self.dx = 1
            self.y = (8-self.y) % 8
            ret = 0xc3
        elif self.x > 6:
            self.dx = -1
            self.y = 7 - self.y
            ret = 0xd8
        else:
            ret = Seed.seedMap[self.y][self.x]

        self.x += self.dx
        if self.index == 0x8000 or (self.index > 0x8000 and (self.index + 1) % 0x8000 == 0):
            return self.next_mask()
        return ret


class Decoder(object):
    """Identify file types and decode known types"""

    def __init__(self, **kwargs):
        self.ptn_mp3 = re.compile(r'\.(qmc3|qmc0|qmcogg)$')
        self.ptn_flac = re.compile(r'\.qmcflac$')
        self.output_dir = kwargs['output_dir']

    def _output_path(self, path):
        if self.output_dir is None:
            return path
        else:
            filename = os.path.basename(path)
            return os.path.join(self.output_dir, filename)

    def _do_decode(self, filename, filebytes):
        d = io.BytesIO()
        seed = Seed()
        for c in filebytes:
            b = seed.next_mask() ^ c
            d.write(struct.pack('<B', b))
        d.flush()
        d.seek(0)
        return d.read()

    def _check(self, filename):
        if (match:=self.ptn_mp3.search(filename)):
            output_fn = filename[:match.start()] + '.mp3'
        elif (match:=self.ptn_flac.search(filename)):
            output_fn = filename[:match.start()] + '.flac'
        else:
            logging.debug('Cannot process filetype %s', os.path.splitext(filename)[-1])
            return None
        return self._output_path(output_fn)

    def _read(self, filename):
        with open(filename, 'rb') as f:
            return f.read()

    def _write(self, output_fn, decoded):
        with open(output_fn, 'wb') as o:
            o.write(decoded)
            o.flush()

    def _file(self, filename):
        output_fn = self._check(filename)
        if not output_fn:
            return
        fb = self._read(filename)
        decoded = self._do_decode(output_fn, fb)
        self._write(output_fn, decoded)

    def _io(self, path):
        with concurrent.futures.ProcessPoolExecutor() as ex:
            futures = {}
            count = 0
            for d, _, files in os.walk(path):
                for f in files:
                    f = os.path.join(d, f)
                    if (of := self._check(f)) is None:
                        continue
                    fb = self._read(f)
                    future = ex.submit(self._do_decode, of, fb)
                    futures[future] = of
                    count += 1
            pbar = tqdm(total=count, unit="file", desc="Decoding...")
            for future in concurrent.futures.as_completed(futures):
                fb = future.result()
                of = futures[future]
                self._write(of, fb)
                pbar.update(1)
                pbar.set_description_str(os.path.basename(of))
            pbar.close()

    def decode(self, path):
        if not os.path.exists(path):
            logging.error(f'{path} does not exist.')

        if os.path.isdir(path):
            self._io(path)
        else:
            self._file(path)


@click.command()
@click.argument('path')
@click.option('--output-dir', default=None)
def decode(path, **kwargs):
    if not os.path.exists(path):
        logging.error('%s does not exist!', path)
        import sys
        sys.exit(1)

    decoder = Decoder(**kwargs)

    if 'path' not in kwargs:
        kwargs['path'] = path

    if (odir := kwargs.get('output_dir')) is not None:
        if not os.path.exists(odir):
            logging.info('Creating output directory: %s', odir)
            os.makedirs(odir, mode=0o755, exist_ok=True)

    decoder.decode(path)


if __name__ == '__main__':
    decode()
