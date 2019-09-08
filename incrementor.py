#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
Incrementor for Sublime Text 3
Created on 25-Sep-2014 by Sanchit Karve
A Sublime Text 3 Plugin that can generate a sequence of numbers and letters using search and replace.

Ported to ST3 from Incrementor for ST2 created on 10-Jul-2012 by eBookArchitects
https://github.com/eBookArchitects/Incrementor

@copy: [Creative Commons Attribution 2.0 Generic](http://creativecommons.org/licenses/by/2.0/)
@python-ver: Python 2.6
"""
import sublime
import sublime_plugin
import re
from functools import partial
from types import GeneratorType


class State(object):
    last_find_input = ""
    last_replace_input = ""
    selected_regions = []


def on_cancel(view):
    view.erase_regions( 'Incrementor' )
    view.sel().add_all( State.selected_regions )


class IncrementorCommand(sublime_plugin.TextCommand):
    """"""
    def window(self):
        """"""
        return self.view.window()

    def match_gen(self, regex):
        """"""
        position = 0
        maximum_replacements = 200

        while True:
            region = self.view.find(regex, position)
            maximum_replacements -= 1

            if region and maximum_replacements > 0:
                yield region

                if region.size() > 2:
                    position = region.end() - 1
                else:
                    position = region.end()

            else:
                break

    def make_alpha_step(self, start='a', step=1, repeat_after='z'):
        """"""
        # optional repeat_after argument specifies the limit of the incrementation.
        # after the limit is reached, return to the start value and resume incrementing
        num = start
        while True:
            yield num
            # No validation here. Use carefully.
            num = chr(ord(num) + step)
            # return to start value if we're past repeat_after
            if repeat_after:
                if step < 0:
                    if num < repeat_after:
                        num = start
                else:
                    if num > repeat_after:
                        num = start

    def make_step(self, start=1, step=1, repeat_after=None):
        """"""
        # optional repeat_after argument specifies the limit of the incrementation.
        # after the limit is reached, return to the start value and resume incrementing
        num = start
        while True:
            yield num
            num = num + step
            if repeat_after:  # return to start value if we're past repeat_after
                if step < 0:
                    if num < repeat_after:
                        num = start
                else:
                    if num > repeat_after:
                        num = start

    def inc_replace(self, pattern_list, match):
        """"""
        replace_string = ''
        for i in range(len(pattern_list)):
            if isinstance(pattern_list[i], GeneratorType):
                replace_string = replace_string + str(next(pattern_list[i]))
            else:
                replace_string = replace_string + match.expand(pattern_list[i])
        return replace_string

    def parse_replace(self, replace):
        """"""
        replace_list = re.split(r'(\\[iaA]\(.+?\)|\\[iaA])', replace)
        replace_list[:] = [item for item in replace_list if item != '']
        for i in range(len(replace_list)):
            if replace_list[i] == '\\i':
                replace_list[i] = self.make_step()
            elif replace_list[i] == '\\a':
                replace_list[i] = self.make_alpha_step(start='a', repeat_after='z')
            elif replace_list[i] == '\\A':
                replace_list[i] = self.make_alpha_step(start='A', repeat_after='Z')
            elif re.match(r'^\\[i]\(.+?\)$', replace_list[i]):
                arg_list = [int(num) for num in re.split(r'\\i|\(|,| |\)', replace_list[i]) if num != '']
                if len(arg_list) == 3:
                    replace_list[i] = self.make_step(start=arg_list[0], step=arg_list[1], repeat_after=arg_list[2])
                elif len(arg_list) == 2:
                    replace_list[i] = self.make_step(start=arg_list[0], step=arg_list[1])
                else:
                    replace_list[i] = self.make_step(start=arg_list[0])

        return replace_list

    def run(self, edit, regex_to_find, replace_matches_with):
        """"""
        positiveMatch = []
        # print( "debug, 1 regex_to_find", regex_to_find, 'replace_matches_with', replace_matches_with )

        def regionSort(thisList):
            """"""

            # print( "debug, 2 thisList", thisList )
            for region in thisList:
                currentBegin = region.begin()

                # print( "debug, 3 currentBegin", currentBegin )
                currentEnd = region.end()

                # print( "debug, 4 currentEnd", currentEnd )
                if currentBegin > currentEnd:

                    region = sublime.Region(currentEnd, currentBegin)
                    # print( "debug, 5 region", region )

            # print( "debug, 6" )
            return sorted(thisList, key=lambda region: region.begin())

        startRegions = self.view.get_regions('Incrementor')

        # print( "debug, 7 startRegions", startRegions )
        startRegions = regionSort(startRegions)

        # print( "debug, 8" )
        view = self.view

        # print( "debug, 9" )
        reFind = re.compile(regex_to_find)

        # print( "debug, 10 reFind", reFind )
        myReplace = self.parse_replace(replace_matches_with)

        # print( "debug, 11 myReplace", myReplace )
        nEmptyRegions = []

        # print( "debug, 12" )
        if startRegions and replace_matches_with:
            # print( "debug, 13, Check if regions are in the given selections" )
            positiveMatch = []

            # print( "debug, 14, Create list of non-empty regions" )
            nEmptyRegions = [sRegion for sRegion in startRegions if not sRegion.empty()]


        # print( "debug, 15 startRegions", startRegions )
        # print( "debug, 16 If there is at least one empty region proceed to check in matches are in region" )
        if len(nEmptyRegions) == 0:

            # print( "debug, 17" )
            positiveMatch = self.match_gen(regex_to_find)

            for match in positiveMatch:

                # print( "debug, 18 match", match )
                myString = view.substr(match)

                # print( "debug, 19 myString", myString )
                newString = reFind.sub(partial(self.inc_replace, myReplace), myString)

                # print( "debug, 20 newString", newString )
                view.replace(edit, match, newString)
        else:

            # print( "debug, 21" )
            adjust = 0
            for sRegion in startRegions:

                # print( "debug, 22 sRegion", sRegion )
                matchRegions = self.match_gen(regex_to_find)

                # print( "debug, 23 adjust", adjust )
                if adjust:
                    # print( "debug, 24 matchRegions", matchRegions )
                    newBeg = sRegion.begin() + adjust

                    # print( "debug, 25 newBeg", newBeg )
                    newEnd = sRegion.end() + adjust

                    # print( "debug, 26 newEnd", newEnd )
                    sRegion = sublime.Region(newBeg, newEnd)

                    # print( "debug, 27 sRegion", sRegion )

                # print( "debug, 28" )
                for mRegion in matchRegions:

                    # print( "debug, 29" , mRegion)
                    if sRegion.contains(mRegion):

                        # print( "debug, 30" , sRegion)
                        myString = view.substr(mRegion)

                        # print( "debug, 31" , myString)
                        newString = reFind.sub(partial(self.inc_replace, myReplace), myString)

                        # print( "debug, 32" , newString)
                        view.erase(edit, mRegion)

                        # print( "debug, 33" )
                        charLen = view.insert(edit, mRegion.begin(), newString)

                        # print( "debug, 34" , charLen)
                        adjustment = charLen - mRegion.size()

                        # print( "debug, 35" )
                        adjust = adjust + adjustment

                        # print( "debug, 36" , adjust)
                        newEnd = sRegion.end() + adjustment

                        # print( "debug, 37" , newEnd)
                        sRegion = sublime.Region(sRegion.begin(), newEnd)

                        # print( "debug, 38" , sRegion)

        # print( "debug, 39 positiveMatch", positiveMatch )
        for match in positiveMatch:

            # print( "debug, 40 match", match )
            myString = view.substr(match)

            # print( "debug, 41 myString", myString )
            newString = reFind.sub(partial(self.inc_replace, myReplace), myString)

            # print( "debug, 42 newString", newString )
            view.replace(edit, match, newString)

        # print( "debug, 43" )
        on_cancel( view )


class IncrementorHighlightCommand(sublime_plugin.TextCommand):
    """Highlights regions or regular expression matches."""

    def run(self, edit, regex=None):
        view = self.view
        startRegions = State.selected_regions

        if startRegions and regex:
            matchRegions = view.find_all(regex)
            # Check if regions are in the given selections.
            positiveMatch = []
            # Create list of non-empty regions.
            nEmptyRegions = [sRegion for sRegion in startRegions if not sRegion.empty()]
            # If there is at least one empty region proceed to check in matches are in region.
            if len(nEmptyRegions) == 0:
                positiveMatch = matchRegions
            else:
                for mRegion in matchRegions:
                    for sRegion in startRegions:
                        if sRegion.contains(mRegion):
                            positiveMatch.append(mRegion)

            view.add_regions('Incrementor', positiveMatch, 'comment', '', sublime.DRAW_OUTLINED)
        else:
            view.erase_regions('Incrementor')


class IncrementorPromptCommand(sublime_plugin.WindowCommand):
    """Prompts for find and replace strings."""

    def highlighter(self, regex=None):
        view=self.window.active_view()
        if regex:
            State.last_find_input = regex
        view.run_command( 'incrementor_highlight', { 'regex': regex } )

    def on_cancel(self):
        on_cancel(self.window.active_view())

    def show_find_panel(self):
        self.window.show_input_panel('Find (w/ RegEx) :', State.last_find_input, on_done=self.find_callback_on_done, on_change=self.highlighter, on_cancel=self.on_cancel)

    def find_callback_on_done(self, find):
        self.regex_to_find = find
        State.last_find_input = find
        self.show_replace_panel()

    def show_replace_panel(self):
        self.window.show_input_panel('Replace (w/o RegEx) :', State.last_replace_input, on_done=self.replace_callback_on_done, on_cancel=self.on_cancel, on_change=None)

    def replace_callback_on_done(self, replace):
        self.replace_matches_with = replace
        State.last_replace_input = replace

        # Call IncrementorCommand to actually make the replacements
        self.window.active_view().run_command('incrementor', {'regex_to_find': self.regex_to_find, 'replace_matches_with': self.replace_matches_with})

    def run(self):
        """"""
        self.window.active_view().erase_regions('Incrementor')
        State.selected_regions = []
        selections = self.window.active_view().sel()

        if selections:
            first_selection = selections[0]

            for selection in selections:
                region = sublime.Region(selection.end(), selection.begin())
                State.selected_regions.append(region)

            selections.clear()
            selections.add( sublime.Region( first_selection.begin(), first_selection.begin() ) )

        self.show_find_panel()
