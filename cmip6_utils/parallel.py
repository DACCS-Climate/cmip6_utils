class MPPartition(object):
    """
    Helps partition a range of values into ranges to be worked on by
    various processors.
    """

    def __init__(self, start, end, nprocs):
        """
        Args:
            start - start number/index
            end - end number/index
            nprocs - number of processors
        """
        self.start = start
        self.end = end
        self.nprocs = nprocs

        # The total number of indices in the range provided
        self.N = self.end - self.start
        # Floor of the number of indices per processor
        self.idxpp = self.N // self.nprocs

    def get_partition(self, i, printdecomp=False):
        """
        Get the details of paritition for a processor given by index i.
        Args:
            i - processor index
        Returns:
            Index at which this processor should start work
            Index at which this processor should end work
            Offset which means how offset the start index of this processor's
                   work is with respect to the global start index. i.e. with respect to
                   self.start
        """
        assert 0 <= i < self.nprocs

        thisStart = self.start + self.idxpp * i
        # Calculating the appropriate stop index for the process
        if i != (self.nprocs - 1):
            thisEnd = self.start + self.idxpp * (i + 1)
        else:
            thisEnd = self.end

        thisOffset = thisStart - self.start
        total = thisEnd - thisStart

        if printdecomp:
            if i == 0:
                print("Multiprocessing decomposition:")
                print("                  Range     Total  Offset")
            print(
                "Processor {0:>2d}: {1:>5d} - {2:<5d} {3:<3d}    {4:<5d}".format(
                    i, thisStart, thisEnd, total, thisOffset
                )
            )

        return thisStart, thisEnd, thisOffset
