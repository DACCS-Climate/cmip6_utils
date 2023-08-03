from typing import Optional

from netCDF4 import Dataset, Variable

__all__ = ["copy_dimension_definitions", "copy_variable_definitions", "copy_file_metadata", "bulk_copy_variable_data"]


def make_chunks(ncf: Dataset, var: Variable, user_chunks: Optional[dict[str, int]] = None) -> tuple:
    if not user_chunks:
        user_chunks = {}

    chunks = []
    for dim_name in var.dimensions:
        dimlen = len(ncf.dimensions[dim_name])

        if dim_name in user_chunks.keys():
            chunks.append(user_chunks[dim_name])
        else:
            if dim_name in ["time", "plev", "lev"]:
                chunks.append(1)
            else:
                chunks.append(dimlen)

    return tuple(chunks)


def copy_dimension_definitions(ncf: Dataset, oncf: Dataset) -> None:
    for dim in ncf.dimensions:
        oncf.createDimension(dim, None if dim == "time" else len(ncf.dimensions[dim]))


def copy_variable_definitions(
    ncf: Dataset,
    oncf: Dataset,
    exclude: Optional[list] = [],
    user_chunks: Optional[dict[str, int]] = None,
    deflate: Optional[int] = 4,
) -> None:
    for var_name in ncf.variables:
        if var_name in exclude:
            continue

        var = ncf[var_name]
        chunking = var.chunking()
        try:
            filters = var.filters()
            complevel = filters["complevel"]
        except TypeError:
            complevel = 0

        fill_value = var._FillValue if hasattr(var, "_FillValue") else None

        if chunking == "contiguous":
            chunks = None
            contiguous = True
        else:
            chunks = make_chunks(ncf, var, user_chunks)
            contiguous = False

        var_ndim = var.ndim
        if var_ndim <= 1:
            complevel = 0
        else:
            complevel = max(complevel, deflate)

        # print(f"Variable: {var_name}")
        # print(f"contig: {contiguous}")
        # print(f"Chunking as: {chunks}")
        # print(f"complevel: {complevel}")

        if chunking == "contiguous":
            complevel = 0

        # print(var_name, var.datatype, var.dimensions, contiguous, chunks, complevel, fill_value)

        ovar = oncf.createVariable(
            var_name,
            var.datatype,
            dimensions=var.dimensions,
            contiguous=contiguous,
            chunksizes=chunks,
            complevel=complevel,
            zlib=True if complevel > 0 else False,
            fill_value=fill_value,
        )

        ovar.setncatts(var.__dict__)


def copy_file_metadata(oncf: Dataset, metadata: dict):
    oncf.setncatts(metadata)


def bulk_copy_variable_data(ncf: Dataset, oncf: Dataset, exclude: Optional[list] = [], time_offset: Optional[int] = 0):
    for var_name in oncf.variables:
        if var_name in exclude:
            continue

        ovar = oncf.variables[var_name]
        ivar = ncf.variables[var_name]

        if "time" in ivar.dimensions:
            ovar[time_offset : time_offset + len(ivar)] = ivar[:]
        else:
            ovar[:] = ivar[:]
