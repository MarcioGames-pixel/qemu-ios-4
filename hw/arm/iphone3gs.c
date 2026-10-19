/*
 * Apple iPhone 3GS (iPhone2,1 / N88AP) early board scaffold.
 *
 * This deliberately models only the known CPU/memory foundation. It does
 * not claim to emulate the S5L8920 peripherals or the iOS boot chain yet.
 *
 * SPDX-License-Identifier: GPL-2.0-or-later
 */

#include "qemu/osdep.h"
#include "hw/arm/machines-qom.h"
#include "hw/core/boards.h"
#include "hw/misc/unimp.h"
#include "system/address-spaces.h"
#include "qemu/error-report.h"
#include "qemu/module.h"
#include "qemu/units.h"
#include "target/arm/cpu.h"

#define TYPE_IPHONE3GS_MACHINE MACHINE_TYPE_NAME("iphone3gs")
OBJECT_DECLARE_SIMPLE_TYPE(IPhone3GSMachineState, IPHONE3GS_MACHINE)

#define IPHONE3GS_DRAM_BASE       0x40000000ULL
#define IPHONE3GS_DRAM_SIZE       (256 * MiB)
#define IPHONE3GS_SRAM_BASE       0x84000000ULL
#define IPHONE3GS_SRAM_SIZE       (256 * KiB)
#define IPHONE3GS_DRAM_LO_SIZE    0x1000

struct IPhone3GSMachineState {
    MachineState parent_obj;
    ARMCPU *cpu;
    MemoryRegion sram;
    MemoryRegion dram_lo;
};

static void iphone3gs_init(MachineState *machine)
{
    IPhone3GSMachineState *s = IPHONE3GS_MACHINE(machine);
    MemoryRegion *sysmem = get_system_memory();
    Object *cpuobj;

    if (machine->ram_size != IPHONE3GS_DRAM_SIZE) {
        error_report("iphone3gs: this prototype currently requires exactly 256 MiB RAM");
        exit(1);
    }

    cpuobj = object_new(machine->cpu_type);
    s->cpu = ARM_CPU(cpuobj);
    object_property_set_link(cpuobj, "memory", OBJECT(sysmem), &error_fatal);
    object_property_set_bool(cpuobj, "has_el3", false, NULL);
    object_property_set_bool(cpuobj, "has_el2", false, NULL);
    object_property_set_bool(cpuobj, "realized", true, &error_fatal);
    object_unref(cpuobj);

    /* N88AP DRAM starts at 0x40000000. Physical page zero aliases its first
     * page on the S5L8920 family; iOS uses this during early vector setup. */
    memory_region_add_subregion(sysmem, IPHONE3GS_DRAM_BASE, machine->ram);
    memory_region_init_alias(&s->dram_lo, OBJECT(machine),
                             "iphone3gs.dram-low-alias", machine->ram, 0,
                             IPHONE3GS_DRAM_LO_SIZE);
    memory_region_add_subregion(sysmem, 0, &s->dram_lo);

    memory_region_init_ram(&s->sram, OBJECT(machine), "iphone3gs.sram",
                           IPHONE3GS_SRAM_SIZE, &error_fatal);
    memory_region_add_subregion(sysmem, IPHONE3GS_SRAM_BASE, &s->sram);

    /*
     * The S5L8920 peripheral window is intentionally an unimplemented trap
     * region. Individual devices must replace it as they are ported and
     * tested. This avoids silently reusing S5L8900/iPhone 3G register models.
     */
    create_unimplemented_device("iphone3gs.s5l8920-peripherals",
                                0x80000000, 0x40000000);
}

static void iphone3gs_class_init(ObjectClass *oc, const void *data)
{
    static const char * const valid_cpu_types[] = {
        ARM_CPU_TYPE_NAME("cortex-a8"),
        NULL,
    };
    MachineClass *mc = MACHINE_CLASS(oc);

    mc->desc = "Apple iPhone 3GS (iPhone2,1 / N88AP; early hardware scaffold)";
    mc->init = iphone3gs_init;
    mc->default_cpu_type = ARM_CPU_TYPE_NAME("cortex-a8");
    mc->valid_cpu_types = valid_cpu_types;
    mc->default_ram_size = IPHONE3GS_DRAM_SIZE;
    mc->default_ram_id = "iphone3gs.dram";
    mc->max_cpus = 1;
    mc->no_floppy = true;
    mc->no_cdrom = true;
}

static const TypeInfo iphone3gs_machine_type = {
    .name = TYPE_IPHONE3GS_MACHINE,
    .parent = TYPE_MACHINE,
    .instance_size = sizeof(IPhone3GSMachineState),
    .class_init = iphone3gs_class_init,
    .interfaces = arm_machine_interfaces,
};

static void iphone3gs_machine_register_types(void)
{
    type_register_static(&iphone3gs_machine_type);
}

type_init(iphone3gs_machine_register_types)
