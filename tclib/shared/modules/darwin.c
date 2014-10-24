/**
Copyright 2010, 2011 Gavin Beatty <gavinbeatty@gmail.com>

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
of the Software, and to permit persons to whom the Software is furnished to do
so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
*/
#include <sys/time.h>

#include <mach/clock.h>
#include <mach/clock_types.h>
#include <mach/mach_host.h>
#include <mach/clock.h>

int darwin_clock_gettime_MONOTONIC(struct timespec *tp)
{
    clock_serv_t clock_ref;
    mach_timespec_t tm;
    host_name_port_t self = mach_host_self();
    memset(&tm, 0, sizeof(tm));
    if (KERN_SUCCESS != host_get_clock_service(self, SYSTEM_CLOCK, &clock_ref))
    {
        return -1;
    }
    if (KERN_SUCCESS != clock_get_time(clock_ref, &tm))
    {
        mach_port_deallocate(mach_task_self(), self);
        return -1;
    }
    mach_port_deallocate(mach_task_self(), self);
    mach_port_deallocate(mach_task_self(), clock_ref);
    tp->tv_sec = tm.tv_sec;
    tp->tv_nsec = tm.tv_nsec;
    return 0;
}

