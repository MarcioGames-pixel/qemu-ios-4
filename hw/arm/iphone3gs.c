/*
 * Apple iPhone 3GS (iPhone2,1 / N88AP) early board model.
 *
 * CPU, memory, CHIPID and an optional externally supplied boot ROM are modeled.
 * S5L8920 peripherals, NAND/NOR controllers and the iOS boot chain remain
 * incomplete; this is not yet an iOS-capable emulator.
 *
 * SPDX-License-Identifier: GPL-2.0-or-later
 */

#include "qemu/osdep.h"
#include "qemu/datadir.h"
#include "hw/arm/machines-qom.h"
#include "hw/core/boards.h"
#include "hw/core/loader.h"
#include "hw/core/sysbus.h"
#include "hw/core/irq.h"
#include "hw/arm/ipod_touch_spi.h"
#include "hw/arm/ipod_touch_nor_spi.h"
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
#define IPHONE3GS_BOOTROM_BASE    0x00000000ULL
#define IPHONE3GS_BOOTROM_SIZE    (64 * KiB)
#define IPHONE3GS_SPI0_BASE       0x82000000ULL
#define IPHONE3GS_SPI0_SIZE       0x100
#define IPHONE3GS_VIC_BASE(n)     (0xbf200000ULL + (n) * 0x10000ULL)
#define IPHONE3GS_VIC_COUNT        3
#define IPHONE3GS_VIC_SIZE         0x1000
#define IPHONE3GS_PMGR_BASE       0xbf100000ULL
#define IPHONE3GS_PMGR_SIZE       0x2000
#define IPHONE3GS_CHIPID_BASE     0xbf500000ULL
#define IPHONE3GS_CHIPID_SIZE     0x1000
#define IPHONE3GS_PERIPH_BASE     0x80000000ULL
#define IPHONE3GS_PERIPH_END      0xc0000000ULL

/* N88AP fuse words reported by the public S5L8920 board reference. These are
 * SoC identity values, not a dump of the immutable silicon BootROM. */
static const uint32_t iphone3gs_chipid_words[] = {
    0x31800387, 0x80758000, 0, 0
};

struct IPhone3GSMachineState {
    MachineState parent_obj;
    ARMCPU *cpu;
    MemoryRegion sram;
    MemoryRegion bootrom;
    MemoryRegion chipid;
    char *nor_path;
    char *nor_rw_path;
    DeviceState *vic[IPHONE3GS_VIC_COUNT];
    DeviceState *pmgr;
};

static void iphone3gs_load_bootrom(IPhone3GSMachineState *s,
                                   MachineState *machine)
{
    g_autofree char *filename = NULL;
    ssize_t size;

    /* A missing -bios leaves a zero-filled diagnostic placeholder so that
     * developers can test machine registration. It is not a real BootROM. */
    if (!machine->firmware) {
        warn_report("iphone3gs: no -bios supplied; reset ROM is a zero-filled placeholder, not Apple's BootROM");
        return;
    }

    filename = qemu_find_file(QEMU_FILE_TYPE_BIOS, machine->firmware);
    if (!filename) {
        error_report("iphone3gs: cannot find boot ROM '%s'", machine->firmware);
        exit(EXIT_FAILURE);
    }

    size = load_image_mr(filename, &s->bootrom);
    if (size <= 0 || size > IPHONE3GS_BOOTROM_SIZE) {
        error_report("iphone3gs: -bios file '%s' must be 1..%u bytes",
                     machine->firmware, (unsigned)IPHONE3GS_BOOTROM_SIZE);
        exit(EXIT_FAILURE);
    }
}

static void iphone3gs_init(MachineState *machine)
{
    IPhone3GSMachineState *s = IPHONE3GS_MACHINE(machine);
    MemoryRegion *sysmem = get_system_memory();
    Object *cpuobj;

    if (machine->ram_size != IPHONE3GS_DRAM_SIZE) {
        error_report("iphone3gs: this prototype currently requires exactly 256 MiB RAM");
        exit(EXIT_FAILURE);
    }

    cpuobj = object_new(machine->cpu_type);
    s->cpu = ARM_CPU(cpuobj);
    object_property_set_link(cpuobj, "memory", OBJECT(sysmem), &error_fatal);
    object_property_set_bool(cpuobj, "has_el3", false, NULL);
    object_property_set_bool(cpuobj, "has_el2", false, NULL);
    object_property_set_bool(cpuobj, "realized", true, &error_fatal);
    object_unref(cpuobj);

    memory_region_add_subregion(sysmem, IPHONE3GS_DRAM_BASE, machine->ram);
    memory_region_init_ram(&s->sram, OBJECT(machine), "iphone3gs.sram",
                           IPHONE3GS_SRAM_SIZE, &error_fatal);
    memory_region_add_subregion(sysmem, IPHONE3GS_SRAM_BASE, &s->sram);

    memory_region_init_rom(&s->bootrom, OBJECT(machine), "iphone3gs.bootrom",
                           IPHONE3GS_BOOTROM_SIZE, &error_fatal);
    memory_region_add_subregion(sysmem, IPHONE3GS_BOOTROM_BASE, &s->bootrom);
    iphone3gs_load_bootrom(s, machine);

    memory_region_init_rom(&s->chipid, OBJECT(machine), "iphone3gs.chipid",
                           IPHONE3GS_CHIPID_SIZE, &error_fatal);
    memcpy(memory_region_get_ram_ptr(&s->chipid), iphone3gs_chipid_words,
           sizeof(iphone3gs_chipid_words));
    memory_region_add_subregion(sysmem, IPHONE3GS_CHIPID_BASE, &s->chipid);

    /* PMGR supplies the 24 MHz timebase and two event timers used by the
     * S5L8920 family. Timer IRQ wiring awaits the real interrupt-controller
     * model, but the counter and event registers are now functional. */
    s->pmgr = qdev_new("s5l8920.pmgr");
    sysbus_realize_and_unref(SYS_BUS_DEVICE(s->pmgr), &error_fatal);
    sysbus_mmio_map(SYS_BUS_DEVICE(s->pmgr), 0, IPHONE3GS_PMGR_BASE);

    /*
     * SPI0 drives the N88AP 1 MiB NOR flash. The SPI/NOR models implement
     * serial command, page-program, erase, status and optional persistence.
     */
    {
        DeviceState *spi0 = ipod_touch_spi_create(IPHONE3GS_SPI0_BASE, NULL,
                                                  0, "nor", false);
        IPodTouchSPIState *spi = IPOD_TOUCH_SPI(spi0);
        if (s->nor_path) {
            spi->nor->nor_path = g_strdup(s->nor_path);
        }
        if (s->nor_rw_path && s->nor_rw_path[0]) {
            ipod_touch_nor_spi_open_overlay(spi->nor, s->nor_rw_path,
                                            &error_fatal);
        }
    }

    /*
     * The S5L8920 has three chained PL192-compatible interrupt controllers
     * in the VIC register window. This prototype uses QEMU's PL190 model for
     * the common register interface; exact PL192 quirks and device IRQ routing
     * still need validation against N88AP traces/device-tree data.
     */
    for (int i = 0; i < IPHONE3GS_VIC_COUNT; i++) {
        s->vic[i] = qdev_new("pl190");
        sysbus_realize_and_unref(SYS_BUS_DEVICE(s->vic[i]), &error_fatal);
        sysbus_mmio_map(SYS_BUS_DEVICE(s->vic[i]), 0, IPHONE3GS_VIC_BASE(i));
    }
    sysbus_connect_irq(SYS_BUS_DEVICE(s->vic[0]), 0,
                       qdev_get_gpio_in(DEVICE(s->cpu), ARM_CPU_IRQ));
    sysbus_connect_irq(SYS_BUS_DEVICE(s->vic[0]), 1,
                       qdev_get_gpio_in(DEVICE(s->cpu), ARM_CPU_FIQ));
    qdev_connect_gpio_out(s->vic[1], 0, qdev_get_gpio_in(s->vic[0], 31));
    qdev_connect_gpio_out(s->vic[2], 0, qdev_get_gpio_in(s->vic[1], 31));

    /*
     * The public S5L8920 reference assigns PMGR event timer 0 to AP IRQ 6
     * and timer 1 to IOP IRQ 5. Only timer 0 can be connected correctly in
     * this board scaffold: the IOP VIC and IOP core are not implemented yet.
     * Do not misroute the IOP interrupt into the AP VIC; wire timer 1 when
     * the IOP interrupt-controller path is ported and verified.
     */
    sysbus_connect_irq(SYS_BUS_DEVICE(s->pmgr), 0,
                       qdev_get_gpio_in(s->vic[0], 6));

    /*
     * Keep unimplemented traps away from mapped devices. Most peripheral
     * windows remain placeholders until their register semantics are known.
     */
    create_unimplemented_device("iphone3gs.s5l8920-peripherals-low",
                                IPHONE3GS_PERIPH_BASE,
                                IPHONE3GS_SPI0_BASE - IPHONE3GS_PERIPH_BASE);
    create_unimplemented_device("iphone3gs.s5l8920-peripherals-spi-gap",
                                IPHONE3GS_SPI0_BASE + IPHONE3GS_SPI0_SIZE,
                                IPHONE3GS_PMGR_BASE -
                                (IPHONE3GS_SPI0_BASE + IPHONE3GS_SPI0_SIZE));
    create_unimplemented_device("iphone3gs.s5l8920-peripherals-mid",
                                IPHONE3GS_PMGR_BASE + IPHONE3GS_PMGR_SIZE,
                                IPHONE3GS_VIC_BASE(0) -
                                (IPHONE3GS_PMGR_BASE + IPHONE3GS_PMGR_SIZE));
    create_unimplemented_device("iphone3gs.s5l8920-peripherals-vic-gap",
                                IPHONE3GS_VIC_BASE(0) +
                                IPHONE3GS_VIC_COUNT * 0x10000ULL,
                                IPHONE3GS_CHIPID_BASE -
                                (IPHONE3GS_VIC_BASE(0) +
                                 IPHONE3GS_VIC_COUNT * 0x10000ULL));
    create_unimplemented_device("iphone3gs.s5l8920-peripherals-high",
                                IPHONE3GS_CHIPID_BASE + IPHONE3GS_CHIPID_SIZE,
                                IPHONE3GS_PERIPH_END -
                                (IPHONE3GS_CHIPID_BASE + IPHONE3GS_CHIPID_SIZE));
}

static char *iphone3gs_get_nor(Object *obj, Error **errp)
{
    return g_strdup(IPHONE3GS_MACHINE(obj)->nor_path);
}

static void iphone3gs_set_nor(Object *obj, const char *value, Error **errp)
{
    IPhone3GSMachineState *s = IPHONE3GS_MACHINE(obj);
    g_free(s->nor_path);
    s->nor_path = g_strdup(value);
}

static char *iphone3gs_get_nor_rw(Object *obj, Error **errp)
{
    return g_strdup(IPHONE3GS_MACHINE(obj)->nor_rw_path);
}

static void iphone3gs_set_nor_rw(Object *obj, const char *value, Error **errp)
{
    IPhone3GSMachineState *s = IPHONE3GS_MACHINE(obj);
    g_free(s->nor_rw_path);
    s->nor_rw_path = g_strdup(value);
}

static void iphone3gs_finalize(Object *obj)
{
    IPhone3GSMachineState *s = IPHONE3GS_MACHINE(obj);
    g_free(s->nor_path);
    g_free(s->nor_rw_path);
}

static void iphone3gs_class_init(ObjectClass *oc, const void *data)
{
    static const char * const valid_cpu_types[] = {
        ARM_CPU_TYPE_NAME("cortex-a8"),
        NULL,
    };
    MachineClass *mc = MACHINE_CLASS(oc);

    mc->desc = "Apple iPhone 3GS (iPhone2,1 / N88AP; early hardware model)";
    mc->init = iphone3gs_init;
    mc->default_cpu_type = ARM_CPU_TYPE_NAME("cortex-a8");
    mc->valid_cpu_types = valid_cpu_types;
    mc->default_ram_size = IPHONE3GS_DRAM_SIZE;
    mc->default_ram_id = "iphone3gs.dram";
    mc->max_cpus = 1;
    mc->no_floppy = true;
    mc->no_cdrom = true;

    object_class_property_add_str(oc, "nor", iphone3gs_get_nor,
                                  iphone3gs_set_nor);
    object_class_property_set_description(
        oc, "nor", "Optional read-only 1 MiB SPI NOR image for N88AP");
    object_class_property_add_str(oc, "nor-rw", iphone3gs_get_nor_rw,
                                  iphone3gs_set_nor_rw);
    object_class_property_set_description(
        oc, "nor-rw", "Optional writable 1 MiB NOR overlay image");
}

static const TypeInfo iphone3gs_machine_type = {
    .name = TYPE_IPHONE3GS_MACHINE,
    .parent = TYPE_MACHINE,
    .instance_size = sizeof(IPhone3GSMachineState),
    .class_init = iphone3gs_class_init,
    .instance_finalize = iphone3gs_finalize,
    .interfaces = arm_machine_interfaces,
};

static void iphone3gs_machine_register_types(void)
{
    type_register_static(&iphone3gs_machine_type);
}

type_init(iphone3gs_machine_register_types)
