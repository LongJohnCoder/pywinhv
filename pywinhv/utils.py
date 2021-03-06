# Axel '0vercl0k' Souchet - Februrary 7th 2019
import pywinhv as whv
import sys
from winhvplatform import *

def IsHypervisorPresent():
    '''Is the support for the Hypervisor Platform APIs
    enabled?'''
    Capabilities = whv.WHV_CAPABILITY()
    Success, _, _ = WHvGetCapability(
        whv.WHvCapabilityCodeHypervisorPresent,
        Capabilities
    )

    return Success and Capabilities.HypervisorPresent == 1

def Align2Page(Size):
    '''Align the size to the next page size.'''
    if (Size % 0x1000) == 0:
        return Size
    return ((Size / 0x1000) + 1) * 0x1000

def Generate32bCodeSegment(Selector = 0x1337):
    '''Generate a 32-bit code ring0 segment.'''
    CsSegment = whv.WHV_REGISTER_VALUE()
    CsSegment.Segment.Base = 0x0
    CsSegment.Segment.Limit = 0xffffffff
    CsSegment.Segment.Selector = Selector
    # SegmentType is 4 bits long, starting at bit8.
    # Bit08: A=Accessed,
    # Bit09: R=Readabale,
    # Bit10: C=Conforming,
    # Bit11: Reserved, has to be 1.
    CsSegment.Segment.SegmentType = 0b1011
    # bit12
    CsSegment.Segment.NonSystemSegment = 1
    CsSegment.Segment.DescriptorPrivilegeLevel = 0
    # P=Present.
    CsSegment.Segment.Present = 1
    # AVL=Available.
    CsSegment.Segment.Available = 0
    # L=Long-mode segment
    CsSegment.Segment.Long = 0
    # D=Default operand size.
    CsSegment.Segment.Default = 1
    # G=Granularity.
    CsSegment.Segment.Granularity = 1
    return CsSegment

def Generate64bUserCodeSegment(Selector = 0x33):
    '''Generate a 64-bit code user segment.'''
    Cs = whv.WHV_REGISTER_VALUE()
    Cs.Segment.Base = 0x0
    Cs.Segment.Limit = 0xffffffff
    Cs.Segment.Selector = Selector
    # SegmentType is 4 bits long, starting at bit8.
    # Bit08: A=Accessed,
    # Bit09: R=Readabale,
    # Bit10: C=Conforming,
    # Bit11: Code, must be 1.
    # XXX: Unclear why clearing the Accessed bit triggers a
    # WHvExitReason.WHvRunVpExitReasonInvalidVpRegisterValue.
    Cs.Segment.SegmentType = 0b1011
    # bit12
    Cs.Segment.NonSystemSegment = 1
    Cs.Segment.DescriptorPrivilegeLevel = 3
    # P=Present.
    Cs.Segment.Present = 1
    # AVL=Available.
    Cs.Segment.Available = 0
    # L=Long-mode segment
    Cs.Segment.Long = 1
    # D=Default operand size.
    Cs.Segment.Default = 0
    # G=Granularity.
    Cs.Segment.Granularity = 1
    return Cs

def Generate64bUserDataSegment(Base = 0, Selector = 0x2b):
    '''Generate a 64-bit data user segment.'''
    Data = whv.WHV_REGISTER_VALUE()
    Data.Segment.Base = Base
    Data.Segment.Limit = 0xffffffff
    Data.Segment.Selector = Selector
    # SegmentType is 4 bits long, starting at bit8.
    # Bit08: A=Accessed,
    # Bit09: W=Writeable,
    # Bit10: E-D=Expand-down,
    # Bit11: Data, must be 0.
    # XXX: Unclear why clearing the Accessed bit triggers a
    # WHvExitReason.WHvRunVpExitReasonInvalidVpRegisterValue.
    Data.Segment.SegmentType = 0b0011
    # bit12
    Data.Segment.NonSystemSegment = 1
    Data.Segment.DescriptorPrivilegeLevel = 3
    # P=Present.
    Data.Segment.Present = 1
    # AVL=Available.
    Data.Segment.Available = 0
    # L=Long-mode segment
    Data.Segment.Long = 1
    # D=Default operand size.
    Data.Segment.Default = 0
    # G=Granularity.
    Data.Segment.Granularity = 1
    return Data

def DumpSegment(Segment):
    '''Dump a segment on stdout.'''
    S = Segment
    print '                    Base:', hex(S.Base)
    print '                   Limit:', hex(S.Limit)
    print '                Selector:', hex(S.Selector)
    print '             SegmentType:', hex(S.SegmentType)
    print '        NonSystemSegment:', hex(S.NonSystemSegment)
    print 'DescriptorPrivilegeLevel:', hex(S.DescriptorPrivilegeLevel)
    print '                 Present:', hex(S.Present)
    print '                     AVL:', hex(S.Available)
    print '                    Long:', hex(S.Long)
    print '                 Default:', hex(S.Default)
    print '             Granularity:', hex(S.Granularity)

def DumpExitContext(ExitContext):
    '''Dump a WHV_RUN_VP_EXIT_CONTEXT on stdout.'''
    E = ExitContext
    print 'ExitReason:', WHvExitReason(E.ExitReason)
    V = E.VpContext
    print 'VpContext.InstructionLength:', hex(V.InstructionLength)
    print 'VpContext.Cr8:', hex(V.Cr8)
    print 'VpContext.Cs:', hex(V.Cs.Selector)
    print 'VpContext.Rip:', hex(V.Rip)
    print 'VpContext.Rflags:', hex(V.Rflags)
    if E.ExitReason == whv.WHvRunVpExitReasonMemoryAccess:
        M = E.MemoryAccess
        print 'MemoryAccess.InstructionByteCount:', hex(M.InstructionByteCount)
        A = M.AccessInfo
        print 'MemoryAccess.AccessInfo.AccessType:', hex(A.AccessType)
        print 'MemoryAccess.AccessInfo.GpaUnmapped:', hex(A.GpaUnmapped)
        print 'MemoryAccess.AccessInfo.GvaValid:', hex(A.GvaValid)
        print 'MemoryAccess.Gpa:', hex(M.Gpa)
        print 'MemoryAccess.Gva:', hex(M.Gva)
    elif E.ExitReason == whv.WHvRunVpExitReasonX64Cpuid:
        C = E.CpuidAccess
        print 'CpuidAccess.Rax:', hex(C.Rax)
        print 'CpuidAccess.Rcx:', hex(C.Rcx)
        print 'CpuidAccess.Rdx:', hex(C.Rdx)
        print 'CpuidAccess.Rbx:', hex(C.Rbx)
        print 'CpuidAccess.DefaultResultRax:', hex(C.DefaultResultRax)
        print 'CpuidAccess.DefaultResultRcx:', hex(C.DefaultResultRcx)
        print 'CpuidAccess.DefaultResultRdx:', hex(C.DefaultResultRdx)
        print 'CpuidAccess.DefaultResultRbx:', hex(C.DefaultResultRbx)
    elif E.ExitReason == whv.WHvRunVpExitReasonException:
        V = E.VpException
        print 'VpException.InstructionByteCount:', hex(V.InstructionByteCount)
        # XXX: UINT8 InstructionBytes[16];
        EI = V.ExceptionInfo
        print 'VpException.ExceptionInfo.ErrorCodeValid:', hex(EI.ErrorCodeValid)
        print 'VpException.ExceptionInfo.SoftwareException:', hex(EI.SoftwareException)
        print 'VpException.ExceptionType:', hex(V.ExceptionType)
        print 'VpException.ErrorCode:', hex(V.ErrorCode)
        print 'VpException.ExceptionParameter:', hex(V.ExceptionParameter)

def CR0(Cr0):
    '''Return a string representation of CR0.'''
    C = Cr0.Reg64
    Bits = {
        0 : 'PE',
        1 : 'MP',
        2 : 'EM',
        3 : 'TS',
        4 : 'ET',
        5 : 'NE',
        16 : 'WP',
        18 : 'AM',
        29 : 'NW',
        30 : 'CD',
        31 : 'PG'
    }
    S = []
    for Bit, Str in Bits.iteritems():
        if (C >> Bit) & 1:
            S.append('CR0.%s' % Str)
    S.append('(%08x)' % C)
    return ' '.join(S)

def CR4(Cr4):
    '''Return a string representation of CR4.'''
    C = Cr4.Reg64
    Bits = {
        0 : 'VME',
        1 : 'PVI',
        2 : 'TSD',
        3 : 'DE',
        4 : 'PSE',
        5 : 'PAE',
        6 : 'MCE',
        7 : 'PGE',
        8 : 'PCE',
        9 : 'OSFXSR',
        10 : 'OSXMMEXCPT',
        11 : 'UMIP',
        12 : 'LA57',
        13 : 'VMXE',
        14 : 'SMXE',
        16 : 'FSGSBASE',
        17 : 'PCIDE',
        18 : 'OSXSAVE',
        20 : 'SMEP',
        21 : 'SMAP',
        22 : 'PKE'
    }
    S = []
    for Bit, Str in Bits.iteritems():
        if (C >> Bit) & 1:
            S.append('CR4.%s' % Str)
    S.append('(%08x)' % C)
    return ' '.join(S)

def GetPfnFromGpa(Gva):
    '''Get the page frame number of the GVA.'''
    return Gva / 0x1000

def SplitAddress(Gva):
    '''Split an address into a page aligned address and its offset.'''
    Page = Gva & 0xfffffffffffff000
    Offset = Gva & 0xfff
    return Page, Offset

def BuildVirtualAddressSpace(Partition, PageGvas, Policy):
    '''This function builds the proper paging structures necessary
    to back a set of GVAs pages.

    Little 'how to 4-level paging':

        * PML4->PDPT->PD->PT,
        * Each entry are 8 bytes long,
        * The virtual-address is broken down like this:
            [Unused - 16 bits][PML4 Index - 9 bits][PDPT Index - 9 bits][PD Index - 9 bits][PT Index - 9 bits][Page Offset - 12 bits]
    '''
    # Ensure page alignment of the GVAs.
    assert all(
        map(lambda Gva: (Gva[0] % 0x1000) == 0, PageGvas)
    ), 'GVAs are expected to be page aligned.'

    PageTables = []

    # Walk the GVA and keep track of the various paging structures
    # we need.
    for PageGva, Access in PageGvas:
        PtIndex   = (PageGva >> (12 + (9 * 0))) & 0b111111111
        PdIndex   = (PageGva >> (12 + (9 * 1))) & 0b111111111
        PdptIndex = (PageGva >> (12 + (9 * 2))) & 0b111111111
        Pml4Index = (PageGva >> (12 + (9 * 3))) & 0b111111111
        PageTables.append((
            PageGva,
            PtIndex,
            PdIndex,
            PdptIndex,
            Pml4Index,
            Access
        ))

    # Those keep track of the various paging structure we have already allocated.
    # The keys of the ledger looks like the following:
    #   - (255) - PML4E=255
    #   - (255, 485) - PML4E=255, PDPTE=485
    #   - (255, 485, 337) - PML4E=255, PDPTE=485, PDE=337
    #   - (255, 485, 337, 353) - PML4E=255, PDPTE=485, PDE=337, PTE=353
    #   - etc.
    # What this means is that we have already allocated a page for the PML4E=255, a page
    # for PML4E=255-PDPTE=485, etc. The values are the (HVA, GPA) of the page.
    Ledger = {}

    def AllocateTableIfNeeded(Idx, Flags = 'rw'):
        '''If an entry is already available in the Ledger, return its addressed.'''
        PageInfo = Ledger.get(Idx, None)
        if PageInfo is not None:
            return PageInfo

        # Allocate backing memory host side.
        Hva, Gpa, _ = Partition.MapGpaRangeWithoutContent(
            Policy.GetGpa(),
            0x1000,
            Flags
        )

        # Feed the information into the appropriate ledger. We keep track
        # of the host address and the GPA.
        Ledger[Idx] = (Hva, Gpa)
        return (Hva, Gpa)

    # We know we need a PML4 table, so allocate it now.
    Pml4Hva, Pml4Gpa, _ = Partition.MapGpaRangeWithoutContent(
        Policy.GetGpa(),
        0x1000,
        'rw'
    )

    # kd> dqs nt!MmUserProbeAddress l1
    # fffff801`790f6da0  00007fff`ffff0000
    IsUserAddress = lambda Gva: Gva <= 0x00007fffffff0000

    for Gva, PtIdx, PdIdx, PdptIdx, Pml4Idx, Access in PageTables:
        # Allocate a page for each level if needed. We allocate the paging structures
        # as rwx. We just map the leaf with the appropriate permissions.
        Idx = (Pml4Idx, )
        PdptHva, PdptGpa = AllocateTableIfNeeded(Idx)
        Idx = (Pml4Idx, PdptIdx)
        PdHva, PdGpa = AllocateTableIfNeeded(Idx)
        Idx = (Pml4Idx, PdptIdx, PdIdx)
        PtHva, PtGpa = AllocateTableIfNeeded(Idx)
        # Make sure to allocate the actual GVA page with proper permissions.
        Idx = (Pml4Idx, PdptIdx, PdIdx, PtIdx)
        GvaHva, GvaGpa = AllocateTableIfNeeded(Idx, Access)

        # print 'Pml4Hva', hex(Pml4Hva), 'Pml4Gpa', hex(Pml4Gpa), 'Pfn', GetPfnFromGpa(Pml4Gpa), 'Pml4e', 255
        # print 'PdptHva', hex(PdptHva), 'PdptGpa', hex(PdptGpa), 'Pfn', GetPfnFromGpa(PdptGpa), 'Pdpte', PdptIdx
        # print '  PdHva', hex(PdHva), '  PdGpa', hex(PdGpa), 'Pfn', GetPfnFromGpa(PdGpa),'  Pde', PdIdx
        # print '  PtHva', hex(PtHva), '  PtGpa', hex(PtGpa), 'Pfn', GetPfnFromGpa(PtGpa), '  Pte', PtIdx
        # print 'PageHva', hex(GvaHva), 'PageGpa', hex(GvaGpa), 'Pfn', GetPfnFromGpa(GvaGpa)
        # Now that we have the memory backing the various levels we
        # link them together.
        TableEntry = whv.MMPTE_HARDWARE()
        TableEntry.AsUINT64 = 0
        TableEntry.Present = 1
        TableEntry.Write = 1
        TableEntry.NoExecute = 0
        TableEntry.UserAccessible = IsUserAddress(Gva)

        # First, the PML4E to the PDPT.
        TableEntry.PageFrameNumber = GetPfnFromGpa(PdptGpa)
        Pml4 = (SIZE_T * 512).from_address(Pml4Hva)
        Pml4[Pml4Idx] = TableEntry.AsUINT64

        # Next, the PDPTE to the PD.
        TableEntry.PageFrameNumber = GetPfnFromGpa(PdGpa)
        Pdpt = (SIZE_T * 512).from_address(PdptHva)
        Pdpt[PdptIdx] = TableEntry.AsUINT64

        # Next, the PDE to the PT.
        TableEntry.PageFrameNumber = GetPfnFromGpa(PtGpa)
        Pd = (SIZE_T * 512).from_address(PdHva)
        Pd[PdIdx] = TableEntry.AsUINT64

        # Finally, the PTE to the Page.
        TableEntry.Write = 'w' in Access
        TableEntry.NoExecute = 'x' not in Access
        TableEntry.PageFrameNumber = GetPfnFromGpa(GvaGpa)
        Pt = (SIZE_T * 512).from_address(PtHva)
        Pt[PtIdx] = TableEntry.AsUINT64

    PageCount = len(Ledger) + 1
    print 'This VA requires', PageCount, 'pages total or', (PageCount * 0x1000) / 1024 / 1024, 'MB'
    return Pml4Gpa

def main(argc, argv):
    pass

if __name__ == '__main__':
    sys.exit(main(len(sys.argv), sys.argv))

