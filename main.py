import asyncio
import inspect
import logging
import os
import traceback
from pathlib import Path
from time import perf_counter

from dotenv import load_dotenv

import dis_snek
from dis_snek import (
    MessageContext,
    Intents,
    listen,
    CMD_BODY,
)

load_dotenv()

logging.basicConfig(
    format="[%(filename)s:%(lineno)d] %(levelname)s - %(message)s",
    datefmt="%m-%d %H:%M:%S",
)
cls_log = logging.getLogger(dis_snek.const.logger_name)
cls_log.setLevel(logging.DEBUG)


class Bot(dis_snek.Snake):
    def __init__(self):
        super().__init__(
            default_prefix="<",
            intents=Intents.ALL,
            asyncio_debug=True,
            sync_interactions=True,
            delete_unused_application_cmds=True,
        )
        self.load_extension("dis_snek.ext.debug_scale")
        self.load_extension("tests.tests")

        self.available: asyncio.Event = asyncio.Event()
        self.available.set()

    @listen()
    async def on_ready(self):
        print(f"Logged in as {self.app.name}")

    @dis_snek.message_command()
    async def begin(self, ctx: MessageContext, arg: CMD_BODY):
        if not self.available.is_set():
            await ctx.send("Waiting for current tests to complete...")
            await self.available.wait()

        if ctx.guild.id == 870046872864165888:
            if ctx.author.id != self.owner.id:
                return await ctx.send(
                    f"Only {self.owner.mention} can use the test suite"
                )

        self.available.clear()

        source = await ctx.send(
            "<a:loading:950666903540625418> Running dis_snek test suite..."
        )
        s = perf_counter()

        methods = inspect.getmembers(self.scales["Tests"], inspect.ismethod)

        for name, method in methods:
            if name.startswith("test_"):
                if arg:
                    if arg.lower() not in name:
                        continue
                test_title = f"{method.__name__.removeprefix('test_')} Tests".title()

                msg = await ctx.send(
                    f"<a:loading:950666903540625418> {test_title}: Running!"
                )
                try:
                    await method(ctx, msg)
                except Exception as e:
                    trace = "\n".join(traceback.format_exception(e))
                    await msg.edit(f"❌ {test_title}: Failed \n```{trace}```")
                else:
                    await msg.edit(f"✅ {test_title}: Completed")

        dur = perf_counter() - s

        await source.edit("✅ Dis_snek Test Suite: Completed")

        await ctx.send(f"Tests completed in {round(dur, 2)} seconds")

        self.available.set()


Bot().start(os.environ.get("TOKEN"))
